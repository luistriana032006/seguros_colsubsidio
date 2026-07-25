"""
Empareja la categoria_top de cada persona con un producto especifico del
catalogo de la Base Maestra (24 productos).

ENTRADA
  Usos_Productos_Afiliados_ETIQUETADO_V3.csv   (500.000 filas, categoria ya calculada)
  hipotesis_producto_estructuradas.csv         (reglas, generadas por estructurar_hipotesis.py)
  catalogo_productos.csv                       (24 productos reales de la Base Maestra)

SALIDA
  Usos_Productos_Afiliados_PRODUCTO_V1.csv     (+4 columnas, nada se sobrescribe)

LOGICA, en este orden
---------------------
0. Si categoria_top == "Sin señal suficiente" no hay nada que emparejar:
   producto_top queda nulo.

1. FILTRO DE ELEGIBILIDAD DURA (antes que cualquier otra cosa)
   Los 3 productos con edad verificada (AP-CHUBB-01, APDIG-CHUBB-01,
   ONCO-CHUBB-01) son todos de Personal y Familiar. Si RANGO_EDAD cae en un
   bucket mas ancho que la regla real ("Menor de 19 años" o "Mayor de 55 años")
   no se puede saber si la persona califica -> pendiente_confirmacion_edad.
   URB-CHUBB-01 no tiene regla de edad, no entra en este filtro.

2. RANKING POR HIPOTESIS DENTRO DE LA CATEGORIA GANADORA
   0 cumplen  -> producto_top = producto general de respaldo de la categoria,
                 producto_indiferenciado = true (se asigno sin evidencia)
   1 cumple   -> ese es producto_top
   2+ cumplen -> todos a productos_alternativos, producto_top = el primero
                 segun el orden del archivo estructurado, indiferenciado = true

3. PRODUCTOS SIN HIPOTESIS DOCUMENTADA
   No se les inventa regla. Solo pueden llegar a producto_top via respaldo, y
   en ese caso ya quedan marcados indiferenciado por el caso "0 cumplen".

Uso:  python3 emparejar_producto.py
"""

import csv
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent  # raiz del repo (este script vive en scripts/)
# v2 (24 jul, 2a ronda): parte de PRODUCTO_V1.csv y recalcula el emparejamiento
# con los productos de declaracion directa fuera del ranking.
ARCHIVO_ENTRADA = BASE / "data" / "processed" / "Usos_Productos_Afiliados_PRODUCTO_V1.csv"
ARCHIVO_HIPOTESIS = BASE / "data" / "catalogo" / "hipotesis_producto_estructuradas.csv"
ARCHIVO_CATALOGO = BASE / "data" / "catalogo" / "catalogo_productos.csv"
ARCHIVO_SALIDA = BASE / "data" / "processed" / "Usos_Productos_Afiliados_PRODUCTO_V2.csv"

SIN_SENAL = "Sin señal suficiente"

# Decision transversal del negocio (24 jul).
PRODUCTO_RESPALDO = {
    "Crédito": "DEUDOR-VIDA-01",
    "Personal y Familiar": "VIDA-01",
    "Hogar": "HOGAR-01",
    # v2: era CARRO-01, que salio del motor de propension. BICI-01 es PROVISIONAL.
    "Movilidad": "BICI-01",
    "Mascotas": "PET-SEG-01",
}

# Buckets de RANGO_EDAD mas anchos que la regla real de Chubb: no se puede
# determinar la elegibilidad sin preguntar la edad exacta.
EDAD_AMBIGUA = ["Menor de 19 años", "Mayor de 55 años"]
PRODUCTOS_CON_REGLA_EDAD = ["AP-CHUBB-01", "APDIG-CHUBB-01", "ONCO-CHUBB-01"]


def norm(texto) -> str:
    """Quita acentos para comparar nombres de categoria entre artefactos.

    Hace falta porque el etiquetado (iteracion 4) escribio la categoria como
    "Credito" sin tilde, mientras que el catalogo y las hipotesis usan
    "Crédito". Sin esto, las 408.900 filas de Credito quedan sin producto.
    """
    if not isinstance(texto, str):
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn").lower().strip()


def cargar_reglas() -> tuple:
    """Lee el CSV estructurado y arma, por producto, sus grupos de condiciones."""
    with ARCHIVO_HIPOTESIS.open(encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    # Productos fuera del ranking: existen en el catalogo pero no compiten.
    directa = sorted({f["producto_id"] for f in filas if f.get("flujo") == "declaracion_directa"})

    propension, orden = {}, []
    for fila in filas:
        if fila["tipo_regla"] != "propension":
            continue
        if fila["producto_id"] in directa:  # guard explicito, no solo implicito
            continue
        pid = fila["producto_id"]
        if pid not in propension:
            propension[pid] = {"categoria": fila["categoria"], "grupos": {}}
            orden.append(pid)
        grupo = int(fila["grupo_and"])
        propension[pid]["grupos"].setdefault(grupo, []).append(
            (fila["columna_dataset"], fila["condicion"])
        )
    return propension, orden, directa


def evaluar_producto(df: pd.DataFrame, grupos: dict) -> pd.Series:
    """Aplica la regla de un producto: OR entre grupos, AND dentro de cada grupo."""
    resultado = pd.Series(False, index=df.index)
    for condiciones in grupos.values():
        grupo_ok = pd.Series(True, index=df.index)
        for columna, condicion in condiciones:
            if condicion == "NO_NULO":
                grupo_ok &= df[columna].notna()
            else:
                grupo_ok &= df[columna].isin(condicion.split("|"))
        resultado |= grupo_ok
    return resultado


def emparejar(df: pd.DataFrame, propension: dict, orden: list) -> pd.DataFrame:
    n = len(df)
    idx = df.index

    # --- PASO 1: filtro de elegibilidad dura ---
    # Los 3 productos con regla de edad son de Personal y Familiar; marcar la
    # duda en filas de otras categorias seria ruido (esos productos no se les
    # van a ofrecer). Ver decisiones_producto_especifico.md.
    edad_ambigua = df["RANGO_EDAD"].isin(EDAD_AMBIGUA)
    pendiente_edad = edad_ambigua & (df["categoria_top"] == "Personal y Familiar")

    # --- PASO 2: cumplimiento de cada producto con hipotesis ---
    cumple = {pid: evaluar_producto(df, cfg["grupos"]) for pid, cfg in propension.items()}

    producto_top = pd.Series(pd.NA, index=idx, dtype="object")
    alternativos = pd.Series("", index=idx, dtype="object")
    indiferenciado = pd.Series(False, index=idx)

    cat_norm = df["categoria_top"].map(norm)

    for categoria, respaldo in PRODUCTO_RESPALDO.items():
        en_categoria = cat_norm == norm(categoria)
        if not en_categoria.any():
            continue

        # Productos de esta categoria, en el orden del archivo estructurado.
        productos_cat = [p for p in orden if norm(propension[p]["categoria"]) == norm(categoria)]

        if not productos_cat:
            # Categoria sin ninguna hipotesis (hoy: Mascotas) -> siempre respaldo.
            producto_top[en_categoria] = respaldo
            indiferenciado[en_categoria] = True
            continue

        matriz = np.column_stack([cumple[p][en_categoria].to_numpy() for p in productos_cat])
        n_cumplen = matriz.sum(axis=1)
        primero = matriz.argmax(axis=1)  # primer True; 0 si ninguno (se corrige abajo)

        elegido = np.array(productos_cat)[primero]
        elegido = np.where(n_cumplen == 0, respaldo, elegido)

        # Lista de los que cumplen, legible, solo cuando hay 2 o mas.
        lista = pd.Series("", index=df.index[en_categoria])
        for j, pid in enumerate(productos_cat):
            aplica = matriz[:, j] & (n_cumplen >= 2)
            sep = np.where((lista != "") & aplica, ", ", "")
            lista = lista + sep + np.where(aplica, pid, "")

        producto_top[en_categoria] = elegido
        alternativos[en_categoria] = lista.to_numpy()
        indiferenciado[en_categoria] = (n_cumplen == 0) | (n_cumplen >= 2)

    # --- PASO 0: sin señal, no hay nada que emparejar ---
    sin_senal = df["categoria_top"] == SIN_SENAL
    producto_top[sin_senal] = pd.NA
    alternativos[sin_senal] = ""
    indiferenciado[sin_senal] = False
    pendiente_edad[sin_senal] = False

    df["producto_top"] = producto_top
    df["productos_alternativos"] = alternativos
    df["pendiente_confirmacion_edad"] = pendiente_edad
    df["producto_indiferenciado"] = indiferenciado

    df.attrs["cumple"] = {p: int(v.sum()) for p, v in cumple.items()}
    df.attrs["edad_ambigua_total"] = int(edad_ambigua.sum())
    _ = n
    return df


def verificacion(df: pd.DataFrame, filas_esperadas: int, propension: dict, directa: list) -> bool:
    print("\n" + "=" * 76)
    print("VERIFICACION")
    print("=" * 76)

    ok_filas = len(df) == filas_esperadas
    print(f"\nFilas de entrada : {filas_esperadas:,}")
    print(f"Filas de salida  : {len(df):,}")
    print(f"Integridad de filas: {'OK - no se perdio ninguna fila' if ok_filas else 'ERROR'}")

    n = len(df)
    sin_senal = (df["categoria_top"] == SIN_SENAL).sum()
    sin_producto = df["producto_top"].isna().sum()
    print(f"\nFilas con categoria_top = '{SIN_SENAL}' : {sin_senal:,}")
    print(f"Filas con producto_top nulo                    : {sin_producto:,}")
    ok_nulos = sin_senal == sin_producto
    print(f"Coinciden exactamente: {'OK' if ok_nulos else 'ERROR'}")

    # --- los productos de declaracion directa NO pueden aparecer ---
    print("\n" + "-" * 76)
    print("DECLARACION DIRECTA: no deben aparecer en producto_top ni en alternativos")
    print("-" * 76)
    tops = set(df["producto_top"].dropna().unique())
    alt_texto = " ".join(df["productos_alternativos"].fillna("").unique())
    ok_directa = True
    for pid in directa:
        en_top = pid in tops
        en_alt = pid in alt_texto
        estado = "OK" if not (en_top or en_alt) else f"ERROR (top={en_top}, alt={en_alt})"
        ok_directa &= not (en_top or en_alt)
        print(f"  {pid:<22} {estado}")
    print(f"  -> los {len(directa)} productos de declaracion directa estan fuera: {'OK' if ok_directa else 'ERROR'}")

    # --- pendiente_confirmacion_edad ---
    print("\n" + "-" * 76)
    print("PENDIENTE_CONFIRMACION_EDAD")
    print("-" * 76)
    pend = df["pendiente_confirmacion_edad"]
    print(f"  Filas marcadas: {pend.sum():,}  ({pend.sum() / n:.3%})")
    edades = df.loc[pend, "RANGO_EDAD"].value_counts()
    for valor, k in edades.items():
        print(f"    {valor:<22} {k:>8,}")
    ok_edad = bool(df.loc[pend, "RANGO_EDAD"].isin(EDAD_AMBIGUA).all())
    print(f"  TODAS caen en {EDAD_AMBIGUA}: {'OK' if ok_edad else 'ERROR'}")
    print(f"  (filas con edad ambigua en toda la base, sin filtrar por categoria: {df.attrs['edad_ambigua_total']:,})")

    # --- producto_indiferenciado ---
    print("\n" + "-" * 76)
    print("PRODUCTO_INDIFERENCIADO, por categoria")
    print("-" * 76)
    ind = df["producto_indiferenciado"]
    print(f"  {'CATEGORIA':<24} {'INDIFERENCIADO':>15} {'TOTAL CAT':>11} {'%':>8}")
    print("  " + "-" * 62)
    cat_norm = df["categoria_top"].map(norm)
    for categoria in list(PRODUCTO_RESPALDO) + [SIN_SENAL]:
        en_cat = cat_norm == norm(categoria)
        total = int(en_cat.sum())
        if total == 0:
            continue
        k = int((ind & en_cat).sum())
        print(f"  {categoria:<24} {k:>15,} {total:>11,} {k / total:>7.2%}")
    print("  " + "-" * 62)
    print(f"  {'TOTAL':<24} {int(ind.sum()):>15,} {n:>11,} {ind.sum() / n:>7.2%}")

    # --- distribucion de producto_top ---
    print("\n" + "-" * 76)
    print("DISTRIBUCION DE producto_top")
    print("-" * 76)
    conteo = df["producto_top"].value_counts(dropna=False)
    for valor, k in conteo.items():
        etiqueta = "(nulo - sin señal)" if pd.isna(valor) else valor
        print(f"  {etiqueta:<24} {k:>8,}  ({k / n:>7.3%})")

    # --- productos que nunca fueron producto_top ---
    print("\n" + "-" * 76)
    print("PRODUCTOS QUE NUNCA APARECIERON COMO producto_top")
    print("-" * 76)
    with ARCHIVO_CATALOGO.open(encoding="utf-8") as f:
        catalogo = list(csv.DictReader(f))
    usados = {v for v in df["producto_top"].dropna().unique()}
    nunca = [(r["producto_id"], r["categoria"]) for r in catalogo if r["producto_id"] not in usados]
    print(f"  {len(nunca)} de {len(catalogo)} productos del catalogo:\n")
    for pid, categoria in nunca:
        if pid in directa:
            motivo = "declaracion directa -> fuera del ranking por decision de negocio"
        elif pid in propension:
            motivo = "tiene hipotesis, pero nunca gano el ranking de su categoria"
        else:
            motivo = "sin hipotesis documentada"
        print(f"    {pid:<20} ({categoria:<20}) {motivo}")

    return ok_filas and ok_nulos and ok_edad and ok_directa


def main() -> None:
    print(f"Leyendo {ARCHIVO_ENTRADA.name} ...")
    df = pd.read_csv(ARCHIVO_ENTRADA)
    filas_esperadas = len(df)

    # Copia del estado previo, para reportar exactamente que cambio.
    previo = df[["producto_top", "productos_alternativos", "producto_indiferenciado"]].copy()

    propension, orden, directa = cargar_reglas()
    print("=" * 76)
    print("REGLAS CARGADAS")
    print("=" * 76)
    print(f"\n{len(propension)} productos COMPITEN en el ranking, en orden de desempate:")
    for pid in orden:
        print(f"  {orden.index(pid) + 1:>2}. {pid:<20} ({propension[pid]['categoria']})")
    print(f"\n{len(directa)} productos en DECLARACION DIRECTA (fuera del ranking):")
    for pid in directa:
        print(f"      {pid}")
    print("\nProducto de respaldo por categoria:")
    for cat, pid in PRODUCTO_RESPALDO.items():
        marca = "  <-- cambio en v2 (era CARRO-01)" if cat == "Movilidad" else ""
        print(f"  {cat:<22} -> {pid}{marca}")

    # Las 4 columnas se recalculan de cero sobre la entrada.
    df = df.drop(columns=["producto_top", "productos_alternativos",
                          "pendiente_confirmacion_edad", "producto_indiferenciado"])
    df = emparejar(df, propension, orden)

    print("\n--- CUANTAS FILAS CUMPLE CADA HIPOTESIS (sobre las 500.000) ---")
    for pid, k in df.attrs["cumple"].items():
        print(f"  {pid:<20} {k:>8,}  ({k / len(df):>7.3%})")

    todo_ok = verificacion(df, filas_esperadas, propension, directa)

    # --- que cambio respecto a la version anterior ---
    print("\n" + "-" * 76)
    print("CAMBIOS RESPECTO A LA VERSION ANTERIOR (V1)")
    print("-" * 76)
    cambio_top = (df["producto_top"].fillna("~") != previo["producto_top"].fillna("~"))
    cambio_alt = (df["productos_alternativos"].fillna("") != previo["productos_alternativos"].fillna(""))
    cambio_ind = (df["producto_indiferenciado"] != previo["producto_indiferenciado"])
    print(f"  Filas con producto_top distinto          : {int(cambio_top.sum()):>8,}")
    print(f"  Filas con productos_alternativos distinto: {int(cambio_alt.sum()):>8,}")
    print(f"  Filas con producto_indiferenciado distinto: {int(cambio_ind.sum()):>8,}")

    if cambio_alt.any():
        print("\n  Combinaciones de alternativos que cambiaron (antes -> ahora), top 8:")
        comp = pd.DataFrame({"antes": previo.loc[cambio_alt, "productos_alternativos"].fillna(""),
                             "ahora": df.loc[cambio_alt, "productos_alternativos"].fillna("")})
        for (antes, ahora), k in comp.value_counts().head(8).items():
            print(f"    {k:>6,}  '{antes}'")
            print(f"            -> '{ahora if ahora else '(vacio)'}'")

    print("\n  producto_top por categoria afectada, antes -> ahora:")
    cat_norm_l = df["categoria_top"].map(norm)
    for categoria in ["Crédito", "Movilidad", "Personal y Familiar"]:
        en_cat = cat_norm_l == norm(categoria)
        print(f"\n    --- {categoria} ({int(en_cat.sum()):,} filas) ---")
        antes = previo.loc[en_cat.to_numpy(), "producto_top"].value_counts(dropna=False)
        ahora = df.loc[en_cat, "producto_top"].value_counts(dropna=False)
        for pid in sorted(set(antes.index.astype(str)) | set(ahora.index.astype(str))):
            a = int(antes.get(pid, 0))
            b = int(ahora.get(pid, 0))
            delta = "" if a == b else f"   ({b - a:+,})"
            print(f"      {pid:<22} {a:>8,} -> {b:>8,}{delta}")

    df.to_csv(ARCHIVO_SALIDA, index=False, encoding="utf-8")
    print(f"\nArchivo generado: {ARCHIVO_SALIDA.name} ({ARCHIVO_SALIDA.stat().st_size / 1e6:.1f} MB, {len(df.columns)} columnas)")
    print(f"El archivo de entrada '{ARCHIVO_ENTRADA.name}' NO fue modificado.")
    print("\nRESULTADO:", "TODAS LAS VERIFICACIONES PASARON" if todo_ok else "*** HAY VERIFICACIONES EN ERROR ***")


if __name__ == "__main__":
    main()

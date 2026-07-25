"""
Etiquetado de las 500.000 filas con score de propension por categoria de seguro.

QUE HACE
--------
Lee el dataset ya limpio y agrega, sin tocar nada existente, un score de
propension [0-1] por cada una de las 5 categorias oficiales (Mascotas, Hogar,
Credito, Movilidad, Personal y Familiar), mas la categoria top, la secundaria
y las reglas legibles que dispararon el score de la top.

Los pesos de este script son una decision de negocio ya cerrada, no una
sugerencia: se ejecutan tal cual fueron especificados. Cualquier mejora
detectada durante la implementacion se documenta como sugerencia aparte en
apuntes/decisiones_etiquetado_hipotesis.md (seccion "Decisiones propias del
agente"), nunca se aplica en silencio.

VERSION 2 (iteracion 5) - corrige los 3 hallazgos de la primera corrida:
  H1 -> Credito pasa de regla binaria (1.0 fijo) a escala graduada por bucket.
  H2 -> Hogar rebalanceado (0.6 + 0.4, VIVIENDA como bonus 0.15, tope 1.0)
        para que el techo llegue a 1.0 y no se quede en 0.70.
  H3 -> Mascotas con score 0.5 exacto (piso fijo, sin correlato de Fuente 3)
        no puede ganar categoria_top; sigue elegible como secundaria.
Sin cambios: pesos de Personal y Familiar y de Movilidad, la regla de
presencia vs. valor, la no renormalizacion y el desempate por confianza.

VERSION 3 (iteracion 6) - filas sin ninguna senal:
  Si las 4 categorias con reglas quedan en 0 y Mascotas esta exactamente en
  su base 0.5, no se fuerza un desempate entre ceros: categoria_top pasa a
  "Sin señal suficiente", categoria_secundaria queda nula y la fila se marca
  requiere_escalamiento=True (columna nueva). Ningun peso cambia respecto a
  la v2, y ninguna otra fila cambia de categoria_top.

REGLA DE NULOS / DESCONOCIDOS
-----------------------------
Si el valor de una columna es "Desconocido" o nulo, la regla que depende de
ese valor se OMITE para esa fila: no suma, no resta.

Excepcion necesaria - reglas de PRESENCIA: en "CIUDAD_AFILIADO no nula" el
nulo ES el dato que la regla evalua, no un dato faltante. Si se omitiera,
Movilidad quedaria sin ninguna regla evaluable en las 288.392 filas sin
ciudad (57,68% de la base) y no seria calculable. Por eso las reglas de
presencia siempre se evaluan; las de VALOR (igualdad / pertenencia) si se
omiten cuando el dato falta. Detalle en el .md, seccion 2.

Uso:  python3 etiquetado_hipotesis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent  # raiz del repo (este script vive en scripts/)
# v2: parte del CSV ya etiquetado de la primera corrida y recalcula las 8
# columnas de score sobre el. No se re-ejecuta la limpieza ni se vuelve al
# Excel. La salida es un archivo nuevo: la v1 se conserva como evidencia del
# "antes" para poder comparar las dos corridas.
ARCHIVO_ENTRADA = BASE / "data" / "processed" / "Usos_Productos_Afiliados_ETIQUETADO_V2.csv"
ARCHIVO_SALIDA = BASE / "data" / "processed" / "Usos_Productos_Afiliados_ETIQUETADO_V3.csv"

# v3: etiqueta para las filas donde ninguna regla de propension se activo.
# No se fuerza un desempate entre ceros: se dice que no hay senal.
SIN_SENAL = "Sin señal suficiente"
TEXTO_SIN_SENAL = "Ninguna regla de propensión se activó con la información disponible"

COL_SALARIO = "RANGO_SALARIAL_LIMPIO"
ETIQUETA_NULO = "Desconocido"

# Las 5 categorias oficiales. El orden es el de confianza de las hipotesis
# declarada en CLAUDE.md (alta -> baja) y se usa para desempatar categoria_top.
CATEGORIAS = [
    ("credito", "Credito"),
    ("personal_familiar", "Personal y Familiar"),
    ("hogar", "Hogar"),
    ("movilidad", "Movilidad"),
    ("mascotas", "Mascotas"),
]

# --- CREDITO (v2): escala graduada por bucket, ya no una regla binaria ---
# Cambio de la iteracion 5. Antes: pertenencia a los 3 buckets bajos -> 1.0 fijo.
# Ahora cada bucket tiene su propio peso, asi el score discrimina dentro del
# grupo de salario bajo en vez de dar 1.00 identico al 75,66% de la base (H1).
# "Desconocido" no esta en la tabla: la regla se omite, como siempre.
CREDITO_POR_BUCKET = {
    "Menor al SMLV": 0.85,
    "Entre 1 y 1.5 SMLV": 1.00,
    "Entre 1.5 y 2 SMLV": 0.90,
    "Entre 2 y 2.5 SMLV": 0.70,
    "Entre 2.5 y 3 SMLV": 0.55,
    "Entre 3 y 4 SMLV": 0.40,
    "Entre 4 y 6 SMLV": 0.25,
    "Entre 6 y 8 SMLV": 0.15,
    "Entre 8 y 10 SMLV": 0.10,
    "Entre 10 y 20 SMLV": 0.05,
    "Entre 20 y 30 SMLV": 0.03,
    "Mayor a 30 SMLV": 0.02,
}

# Usado solo por Mascotas (+0.15). Credito ya no lo usa.
SALARIO_BAJO = ["Menor al SMLV", "Entre 1 y 1.5 SMLV", "Entre 1.5 y 2 SMLV"]
SALARIO_ALTO = [
    "Entre 3 y 4 SMLV",
    "Entre 4 y 6 SMLV",
    "Entre 6 y 8 SMLV",
    "Entre 8 y 10 SMLV",
    "Entre 10 y 20 SMLV",
    "Entre 20 y 30 SMLV",
    "Mayor a 30 SMLV",
]
EDAD_MADURA = ["36 a 45 años", "46 a 55 años", "Mayor de 55 años"]
CIUDADES_PERIFERICAS = ["SOACHA", "MOSQUERA", "ZIPAQUIRA", "FUNZA"]
CIUDAD_PENALIZADA_MASCOTAS = "BUCARAMANGA"


def concatenar_reglas(reglas: list, indice: pd.Index) -> pd.Series:
    """Une en un solo texto legible las etiquetas de las reglas que dispararon.

    reglas: lista de (mascara, etiqueta) donde etiqueta puede ser un string fijo
    o una Serie (para incluir el valor real de la fila, ej. "RANGO_EDAD=46 a 55 años").
    """
    salida = pd.Series("", index=indice)
    for mascara, etiqueta in reglas:
        agregado = pd.Series("", index=indice)
        valores = etiqueta[mascara] if isinstance(etiqueta, pd.Series) else etiqueta
        agregado.loc[mascara] = valores
        separador = np.where((salida != "") & (agregado != ""), ", ", "")
        salida = salida + separador + agregado
    return salida


def calcular_scores(df: pd.DataFrame, top2_grupo_familiar: list) -> tuple:
    """Aplica las reglas de negocio y devuelve (scores, textos de reglas)."""
    idx = df.index
    salario = df[COL_SALARIO]
    ciudad = df["CIUDAD_AFILIADO"]

    # Dato disponible / faltante por columna (para la regla de omision).
    salario_conocido = salario != ETIQUETA_NULO
    ciudad_conocida = ciudad.notna()

    scores, reglas_txt = {}, {}

    # ---------------- CREDITO (v2: escala graduada) ----------------
    # Regla de VALOR: si el salario es Desconocido, la regla se omite (la fila
    # queda en 0.0 por ausencia de evidencia, no por evidencia en contra).
    peso_credito = salario.map(CREDITO_POR_BUCKET)
    m_credito = salario_conocido & peso_credito.notna()
    scores["credito"] = peso_credito.where(m_credito, 0.0).to_numpy()
    # La etiqueta muestra el bucket y el peso que aporto, para que la
    # explicacion diga por que ese score y no otro.
    etiqueta_credito = (
        COL_SALARIO + "=" + salario + " (" + peso_credito.map(lambda p: f"{p:.2f}" if pd.notna(p) else "") + ")"
    )
    reglas_txt["credito"] = concatenar_reglas([(m_credito, etiqueta_credito)], idx)

    # ---------------- PERSONAL Y FAMILIAR ----------------
    # Las 3 columnas tienen 0% de nulos, asi que ninguna regla se omite nunca.
    m_drogueria = df["DROGUERIA"] == "SI"
    m_grupo = df["SEGMENTO_GRUPO_FAMILIAR"].isin(top2_grupo_familiar)
    m_edad = df["RANGO_EDAD"].isin(EDAD_MADURA)
    scores["personal_familiar"] = (
        np.where(m_drogueria, 0.4, 0.0)
        + np.where(m_grupo, 0.3, 0.0)
        + np.where(m_edad, 0.3, 0.0)
    )
    reglas_txt["personal_familiar"] = concatenar_reglas(
        [
            (m_drogueria, "DROGUERIA=SI"),
            (m_grupo, "SEGMENTO_GRUPO_FAMILIAR=" + df["SEGMENTO_GRUPO_FAMILIAR"]),
            (m_edad, "RANGO_EDAD=" + df["RANGO_EDAD"]),
        ],
        idx,
    )

    # ---------------- HOGAR (v2: rebalanceado) ----------------
    # Cambio de la iteracion 5. Antes 0.4 + 0.3 + 0.3 con techo real 0.70,
    # porque VIVIENDA=SI solo existe en 36 filas y la tercera regla casi nunca
    # se activaba (H2). Ahora las dos reglas que si tienen datos suman 1.0 por
    # si solas y VIVIENDA queda como BONUS de 0.15 por encima, con tope en 1.0.
    m_salario_alto = salario_conocido & salario.isin(SALARIO_ALTO)  # regla de VALOR
    m_ciudad_hogar = ciudad_conocida  # regla de PRESENCIA: el nulo es el dato
    m_vivienda = df["VIVIENDA"] == "SI"
    scores["hogar"] = np.minimum(
        1.0,
        np.where(m_salario_alto, 0.6, 0.0)
        + np.where(m_ciudad_hogar, 0.4, 0.0)
        + np.where(m_vivienda, 0.15, 0.0),  # bonus, fuera del presupuesto de 1.0
    )
    reglas_txt["hogar"] = concatenar_reglas(
        [
            (m_salario_alto, COL_SALARIO + "=" + salario),
            (m_ciudad_hogar, "CIUDAD_AFILIADO=" + ciudad.fillna("")),
            (m_vivienda, "VIVIENDA=SI (bonus +0.15)"),
        ],
        idx,
    )

    # ---------------- MOVILIDAD ----------------
    # Regla de PRESENCIA (0.5) + periferica (0.5 adicional) = 1.0 como maximo.
    # Nunca 1.5: la periferica se suma sobre la de presencia y ahi topa.
    m_ciudad_mov = ciudad_conocida
    m_periferica = ciudad.isin(CIUDADES_PERIFERICAS)
    scores["movilidad"] = np.where(m_ciudad_mov, 0.5, 0.0) + np.where(m_periferica, 0.5, 0.0)
    reglas_txt["movilidad"] = concatenar_reglas(
        [
            (m_ciudad_mov & ~m_periferica, "CIUDAD_AFILIADO=" + ciudad.fillna("") + " (conocida)"),
            (m_periferica, "CIUDAD_AFILIADO=" + ciudad.fillna("") + " (periferica)"),
        ],
        idx,
    )

    # ---------------- MASCOTAS ----------------
    # Base fija para todas las filas + ajuste por salario - penalizacion ciudad.
    m_mascotas_salario = salario_conocido & salario.isin(SALARIO_BAJO)  # regla de VALOR
    m_bucaramanga = ciudad == CIUDAD_PENALIZADA_MASCOTAS  # regla de VALOR
    scores["mascotas"] = (
        0.5 + np.where(m_mascotas_salario, 0.15, 0.0) - np.where(m_bucaramanga, 0.15, 0.0)
    )
    reglas_txt["mascotas"] = concatenar_reglas(
        [
            (pd.Series(True, index=idx), "base nacional Mascotas (0.5)"),
            (m_mascotas_salario, COL_SALARIO + "=" + salario),
            (m_bucaramanga, "CIUDAD_AFILIADO=BUCARAMANGA (penalizacion -0.15)"),
        ],
        idx,
    )

    return scores, reglas_txt


def etiquetar(df: pd.DataFrame, top2_grupo_familiar: list) -> pd.DataFrame:
    scores, reglas_txt = calcular_scores(df, top2_grupo_familiar)

    claves = [clave for clave, _ in CATEGORIAS]
    nombres = [nombre for _, nombre in CATEGORIAS]

    for clave in claves:
        df[f"score_{clave}"] = np.round(scores[clave], 2)

    matriz = np.column_stack([df[f"score_{c}"].to_numpy() for c in claves])
    n = len(df)

    # --- Elegibilidad de Mascotas para el primer lugar (v2, cambio it. 5) ---
    # Mascotas con score 0.5 exacto significa que NINGUN correlato de Fuente 3
    # se activo: es el piso fijo, no evidencia. En ese caso no puede ganar el
    # primer lugar (antes ganaba por descarte, H3). Se la excluye SOLO del
    # calculo de categoria_top; sigue compitiendo por categoria_secundaria.
    i_mascotas = claves.index("mascotas")
    mascotas_inelegible = matriz[:, i_mascotas] == 0.5

    matriz_top = matriz.copy()
    matriz_top[mascotas_inelegible, i_mascotas] = -1.0  # fuera del ranking de top

    # Desempate: ante scores iguales gana la categoria de mayor confianza de
    # hipotesis segun CLAUDE.md (orden de CATEGORIAS). np.argsort con kind
    # "stable" preserva ese orden en los empates.
    idx_top = np.argsort(-matriz_top, axis=1, kind="stable")[:, 0]

    # La secundaria se elige sobre las 5 categorias reales menos la que quedo
    # top, para que Mascotas-piso pueda seguir apareciendo como segunda opcion.
    matriz_sec = matriz.copy()
    matriz_sec[np.arange(n), idx_top] = -np.inf
    idx_sec = np.argsort(-matriz_sec, axis=1, kind="stable")[:, 0]

    nombres_arr = np.array(nombres)
    df["categoria_top"] = nombres_arr[idx_top]
    df["categoria_secundaria"] = nombres_arr[idx_sec]

    # --- Filas sin ninguna senal (v3, cambio it. 6) ---
    # Si las 4 categorias con reglas quedaron en 0 y Mascotas esta exactamente
    # en su base (0.5, sin bono ni penalizacion), no hay nada que rankear:
    # cualquier categoria_top saldria de un desempate entre ceros, o sea de la
    # tabla de confianza y no de los datos de la persona. En vez de eso se
    # declara que no hay senal y se marca para escalamiento.
    sin_senal = (
        (df["score_credito"] == 0.0)
        & (df["score_hogar"] == 0.0)
        & (df["score_movilidad"] == 0.0)
        & (df["score_personal_familiar"] == 0.0)
        & (df["score_mascotas"] == 0.5)
    )

    # Las reglas legibles de la categoria que quedo top.
    textos = np.column_stack([reglas_txt[c].to_numpy() for c in claves])
    df["reglas_activadas_top"] = textos[np.arange(len(df)), idx_top]

    # El override de sin senal va DESPUES de asignar reglas_activadas_top,
    # si no la asignacion de arriba lo pisaria y el texto quedaria vacio.
    df.loc[sin_senal, "categoria_top"] = SIN_SENAL
    df.loc[sin_senal, "categoria_secundaria"] = np.nan
    df.loc[sin_senal, "reglas_activadas_top"] = TEXTO_SIN_SENAL
    df["requiere_escalamiento"] = sin_senal

    # Se guardan para el reporte de verificacion, no se escriben al CSV.
    df.attrs["sin_senal"] = int(sin_senal.sum())
    df.attrs["mascotas_inelegible"] = int(mascotas_inelegible.sum())
    maximo = matriz_top.max(axis=1)
    df.attrs["empates_top"] = int(((matriz_top == maximo[:, None]).sum(axis=1) > 1).sum())
    df.attrs["top_score_cero"] = int((maximo <= 0.0).sum())

    return df


def verificacion(df: pd.DataFrame, filas_esperadas: int) -> bool:
    print("\n" + "=" * 72)
    print("VERIFICACION")
    print("=" * 72)

    claves = [clave for clave, _ in CATEGORIAS]
    ok_filas = len(df) == filas_esperadas
    print(f"\nFilas de entrada : {filas_esperadas:,}")
    print(f"Filas de salida  : {len(df):,}")
    print(f"Integridad de filas: {'OK - no se perdio ninguna fila' if ok_filas else 'ERROR'}")

    print("\nRango de cada score (debe estar entre 0 y 1):")
    ok_rango = True
    for clave in claves:
        col = df[f"score_{clave}"]
        dentro = bool(col.min() >= 0.0 and col.max() <= 1.0)
        ok_rango &= dentro
        print(f"  score_{clave:<20} min={col.min():.2f}  max={col.max():.2f}  {'OK' if dentro else 'FUERA DE RANGO'}")

    ok_nulos = not df[[f"score_{c}" for c in claves]].isna().any().any()
    print(f"\nSin nulos en los scores: {'OK' if ok_nulos else 'ERROR'}")

    n = len(df)
    print("\n" + "-" * 72)
    print("RESOLUCION DE categoria_top")
    print("-" * 72)
    inelegible = df.attrs["mascotas_inelegible"]
    empates = df.attrs["empates_top"]
    top_cero = df.attrs["top_score_cero"]
    sin_senal = df.attrs["sin_senal"]
    print(f"  Mascotas excluida del primer lugar (score 0.50 exacto) : {inelegible:>8,}  ({inelegible / n:>7.3%})")
    print(f"  Filas resueltas por desempate                          : {empates:>8,}  ({empates / n:>7.3%})")
    print(f"  Filas cuya categoria_top quedo con score 0.00          : {top_cero:>8,}  ({top_cero / n:>7.3%})")
    print(f"  Filas marcadas '{SIN_SENAL}'              : {sin_senal:>8,}  ({sin_senal / n:>7.3%})")

    # requiere_escalamiento debe coincidir exactamente con esas filas.
    ok_escalamiento = int(df["requiere_escalamiento"].sum()) == sin_senal
    print(f"  requiere_escalamiento=True coincide con esas filas     : {'OK' if ok_escalamiento else 'ERROR'}")

    # Las filas sin senal no deben tener secundaria ni reglas de propension.
    sub = df[df["categoria_top"] == SIN_SENAL]
    ok_nulo_sec = bool(sub["categoria_secundaria"].isna().all())
    ok_texto = bool((sub["reglas_activadas_top"] == TEXTO_SIN_SENAL).all())
    print(f"  categoria_secundaria nula en todas ellas               : {'OK' if ok_nulo_sec else 'ERROR'}")
    print(f"  reglas_activadas_top con el texto de sin senal         : {'OK' if ok_texto else 'ERROR'}")

    # El resto de las filas NO debe haber cambiado respecto a la v2.
    ok_resto = True
    archivo_v2 = BASE / "data" / "processed" / "Usos_Productos_Afiliados_ETIQUETADO_V2.csv"
    if archivo_v2.exists():
        v2 = pd.read_csv(archivo_v2, usecols=["categoria_top", "categoria_secundaria"])
        resto = df["categoria_top"] != SIN_SENAL
        ok_resto = bool(
            df.loc[resto, "categoria_top"].reset_index(drop=True).equals(
                v2.loc[resto.to_numpy(), "categoria_top"].reset_index(drop=True))
            and df.loc[resto, "categoria_secundaria"].reset_index(drop=True).equals(
                v2.loc[resto.to_numpy(), "categoria_secundaria"].reset_index(drop=True))
        )
        cambiadas_v2 = int((df["categoria_top"] != v2["categoria_top"]).sum())
        print(f"\n  Filas que cambiaron de categoria_top respecto a v2     : {cambiadas_v2:>8,}")
        print(f"  Todas las que cambiaron son las de sin senal           : {'OK' if cambiadas_v2 == sin_senal else 'ERROR'}")
        print(f"  El resto de filas es identico a v2 (top y secundaria)  : {'OK' if ok_resto else 'ERROR'}")
        ok_resto = ok_resto and cambiadas_v2 == sin_senal

    ok_escalamiento = ok_escalamiento and ok_nulo_sec and ok_texto and ok_resto

    print("\n" + "-" * 72)
    print("DISTRIBUCION DE categoria_top")
    print("-" * 72)
    conteo = df["categoria_top"].value_counts()
    for _, nombre in CATEGORIAS:
        n = int(conteo.get(nombre, 0))
        marca = "  <-- SIN FILAS" if n == 0 else ("  <-- MUY POCAS" if n < len(df) * 0.001 else "")
        print(f"  {nombre:<22} {n:>8,}  ({n / len(df):>7.3%}){marca}")

    n_sin = int(conteo.get(SIN_SENAL, 0))
    print(f"  {SIN_SENAL:<22} {n_sin:>8,}  ({n_sin / len(df):>7.3%})")

    vacias = [nombre for _, nombre in CATEGORIAS if int(conteo.get(nombre, 0)) == 0]
    if vacias:
        print(f"\n  Nota: categorias que nunca quedan top: {', '.join(vacias)}")
        print("  (Mascotas: decision de negocio ya tomada, no es un bug. Ver decisiones_etiquetado_hipotesis.md § 13)")

    print("\nDISTRIBUCION DE categoria_secundaria")
    conteo_sec = df["categoria_secundaria"].value_counts()
    for _, nombre in CATEGORIAS:
        n = int(conteo_sec.get(nombre, 0))
        print(f"  {nombre:<22} {n:>8,}  ({n / len(df):>7.3%})")

    return ok_filas and ok_rango and ok_nulos and ok_escalamiento


def ejemplos(df: pd.DataFrame) -> None:
    """Imprime una fila real por categoria, con su perfil y por que quedo asi."""
    print("\n" + "=" * 72)
    print("EJEMPLOS REALES - una fila por categoria")
    print("=" * 72)

    perfil_cols = [
        "SERIE", "GENERO", "RANGO_EDAD", COL_SALARIO,
        "SEGMENTO_GRUPO_FAMILIAR", "CIUDAD_AFILIADO", "DROGUERIA", "VIVIENDA",
    ]
    claves = [clave for clave, _ in CATEGORIAS]

    for _, nombre in [*CATEGORIAS, (None, SIN_SENAL)]:
        sub = df[df["categoria_top"] == nombre]
        print(f"\n--- {nombre} ---")
        if sub.empty:
            print("  (ninguna fila quedo con esta categoria como top)")
            continue
        fila = sub.iloc[0]
        print("  PERFIL:")
        for col in perfil_cols:
            valor = fila[col]
            valor = "(nulo)" if pd.isna(valor) else valor
            print(f"    {col:<26} {valor}")
        print("  SCORES:")
        for clave, nom in CATEGORIAS:
            marca = "  <-- TOP" if nom == fila["categoria_top"] else (
                "  <-- SECUNDARIA" if nom == fila["categoria_secundaria"] else "")
            print(f"    {nom:<26} {fila[f'score_{clave}']:.2f}{marca}")
        secundaria = fila["categoria_secundaria"]
        print(f"    categoria_secundaria       {'(nula)' if pd.isna(secundaria) else secundaria}")
        print(f"    requiere_escalamiento      {fila['requiere_escalamiento']}")
        print(f"  POR QUE QUEDO ASI: {fila['reglas_activadas_top']}")
        _ = claves


def main() -> None:
    print(f"Leyendo {ARCHIVO_ENTRADA.name} ...")
    df = pd.read_csv(ARCHIVO_ENTRADA)
    filas_esperadas = len(df)

    print("=" * 72)
    print("DIAGNOSTICO PREVIO")
    print("=" * 72)
    conteo_grupo = df["SEGMENTO_GRUPO_FAMILIAR"].value_counts()
    top2 = conteo_grupo.head(2).index.tolist()
    print("\nSEGMENTO_GRUPO_FAMILIAR (calculado, no asumido):")
    for valor, n in conteo_grupo.items():
        marca = "  <-- top 2" if valor in top2 else ""
        print(f"  {valor:<12} {n:>8,}{marca}")
    print(f"\nTop 2 usados en la regla de Personal y Familiar: {top2}")

    n_salario_desc = (df[COL_SALARIO] == ETIQUETA_NULO).sum()
    n_ciudad_nula = df["CIUDAD_AFILIADO"].isna().sum()
    print(f"\nFilas con {COL_SALARIO} = '{ETIQUETA_NULO}': {n_salario_desc:,} ({n_salario_desc / len(df):.3%})")
    print(f"Filas con CIUDAD_AFILIADO nula        : {n_ciudad_nula:,} ({n_ciudad_nula / len(df):.3%})")
    print("  -> en esas filas se omiten las reglas de VALOR que dependen de esa columna.")

    df = etiquetar(df, top2)
    todo_ok = verificacion(df, filas_esperadas)
    ejemplos(df)

    df.to_csv(ARCHIVO_SALIDA, index=False, encoding="utf-8")
    print(f"\nArchivo generado: {ARCHIVO_SALIDA.name} ({ARCHIVO_SALIDA.stat().st_size / 1e6:.1f} MB)")
    print(f"El archivo de entrada '{ARCHIVO_ENTRADA.name}' NO fue modificado.")
    print("\nRESULTADO:", "TODAS LAS VERIFICACIONES PASARON" if todo_ok else "*** HAY VERIFICACIONES EN ERROR ***")


if __name__ == "__main__":
    main()

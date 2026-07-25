"""
Convierte las hipotesis en prosa de Hipotesis_Generales_Seguros.md a un archivo
estructurado y parseable: hipotesis_producto_estructuradas.csv

POR QUE ESTE PASO EXISTE
------------------------
El .md es prosa pensada para que la lea una persona. Usarlo como fuente de
reglas dentro del motor obligaria a parsear texto libre en tiempo de ejecucion,
que es fragil y no auditable. Este script hace la traduccion una sola vez, deja
el resultado en un CSV, y conserva el texto original de cada celda para poder
verificar despues que la estructuracion no cambio el sentido.

VERSION 2 (24 jul) - el .md se actualizo y resolvio las 10 hipotesis que la v1
habia reportado como no estructurables. Dos decisiones transversales nuevas del
negocio, que este script aplica al pie de la letra:
  - ESCALA UNICA de RANGO_SALARIAL_LIMPIO (Bajo/Medio/Medio-alto/Alto). Toda
    hipotesis que diga "bajo"/"medio"/"alto" usa ESTA escala, no una lectura
    propia por producto.
  - PRODUCTO GENERAL DE RESPALDO por categoria, para el caso "0 productos
    cumplen" del ranking.

FORMATO: una fila por CONDICION ATOMICA (forma normal disyuntiva)
-----------------------------------------------------------------
Las hipotesis nuevas traen reglas compuestas (HOGAR-01 mezcla Y con O), asi que
una sola fila por producto ya no alcanza. Cada fila es una condicion atomica:
  - Las filas del MISMO producto con el MISMO grupo_and se combinan con Y.
  - Los distintos grupo_and de un producto se combinan con O.
Ej. HOGAR-01: grupo 1 = (salario alto Y ciudad conocida); grupo 2 = (vivienda
=SI). El producto aplica si se cumple el grupo 1 O el grupo 2.

Sintaxis de la columna `condicion`:
  - "valor_a|valor_b"  -> la columna debe ser alguno de esos valores
  - "NO_NULO"          -> la columna solo debe tener dato (regla de presencia)

Uso:  python3 estructurar_hipotesis.py
"""

import csv
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # raiz del repo (este script vive en scripts/)
ARCHIVO_SALIDA = BASE / "data" / "catalogo" / "hipotesis_producto_estructuradas.csv"

CAMPOS = ["producto_id", "categoria", "grupo_and", "columna_dataset", "condicion",
          "tipo_regla", "flujo", "texto_original"]

# Flujos posibles de un producto (decision de negocio del 24 jul, 2a ronda):
#   ranking_propension  -> compite por producto_top dentro de su categoria
#   declaracion_directa -> NO pasa por el ranking en absoluto. Existe en el
#                          catalogo, pero solo se ofrece cuando la persona
#                          declara la condicion en conversacion con el bot.
FLUJO_RANKING = "ranking_propension"
FLUJO_DIRECTO = "declaracion_directa"

# ---------------------------------------------------------------------------
# ESCALA UNICA DE RANGO_SALARIAL_LIMPIO (decision transversal del negocio)
# Cualquier hipotesis que diga "bajo"/"medio"/"medio-alto"/"alto" usa esto.
# ---------------------------------------------------------------------------
TIER_BAJO = ["Menor al SMLV", "Entre 1 y 1.5 SMLV", "Entre 1.5 y 2 SMLV"]
TIER_MEDIO = ["Entre 2 y 2.5 SMLV", "Entre 2.5 y 3 SMLV", "Entre 3 y 4 SMLV"]
TIER_MEDIO_ALTO = ["Entre 4 y 6 SMLV", "Entre 6 y 8 SMLV"]
TIER_ALTO = ["Entre 8 y 10 SMLV", "Entre 10 y 20 SMLV", "Entre 20 y 30 SMLV", "Mayor a 30 SMLV"]

# ">1.5 SMLV" del texto de DEUDOR-VIDA-01: todo lo que esta por encima de 1.5,
# o sea el bucket "Entre 1.5 y 2" y todos los superiores.
MAYOR_A_1_5 = ["Entre 1.5 y 2 SMLV"] + TIER_MEDIO + TIER_MEDIO_ALTO + TIER_ALTO

CIUDADES_PERIFERICAS = ["SOACHA", "MOSQUERA", "ZIPAQUIRA", "FUNZA"]
EDAD_36_55 = ["36 a 45 años", "46 a 55 años"]

# APEXEQ-PAL-01: su texto trae su propio alcance explicito por escrito
# ("Menor al SMLV a 1.5 SMLV" = 2 buckets), asi que NO se expande a los 3 del
# tier Bajo. Regla general fijada el 24 jul: la escala unica solo aplica a
# terminos que no traian ya su alcance escrito.
BAJO_EXPLICITO_APEXEQ = ["Menor al SMLV", "Entre 1 y 1.5 SMLV"]

# ---------------------------------------------------------------------------
# PRODUCTO GENERAL DE RESPALDO POR CATEGORIA (decision transversal del negocio)
# Se usa en el ranking cuando ningun producto de la categoria cumple hipotesis.
# ---------------------------------------------------------------------------
PRODUCTO_RESPALDO = {
    "Crédito": "DEUDOR-VIDA-01",
    "Personal y Familiar": "VIDA-01",
    "Hogar": "HOGAR-01",
    # 24 jul (2a ronda): era CARRO-01, que salio del motor de propension.
    # BICI-01 es respaldo PROVISIONAL de Movilidad.
    "Movilidad": "BICI-01",
    "Mascotas": "PET-SEG-01",
}


def cond(valores) -> str:
    return "|".join(valores)


# ---------------------------------------------------------------------------
# 1. ELEGIBILIDAD DURA - dato verificado de los certificados de Chubb
# ---------------------------------------------------------------------------
ELEGIBILIDAD_DURA = [
    ("AP-CHUBB-01", "Personal y Familiar", 1, "RANGO_EDAD", "18 a 65 años + 364 días",
     "Ingreso 18 a 65 años + 364 días; permanencia hasta 69 años + 364 días (cobertura adicional de fracturas)"),
    ("APDIG-CHUBB-01", "Personal y Familiar", 1, "RANGO_EDAD", "18 a 65 años + 364 días",
     "Ingreso 18 a 65 años + 364 días; permanencia hasta 69 años + 364 días"),
    ("ONCO-CHUBB-01", "Personal y Familiar", 1, "RANGO_EDAD", "18 a 64 años + 364 días",
     "Ingreso 18 a 64 años + 364 días; permanencia hasta 65 años + 364 días"),
    ("URB-CHUBB-01", "Personal y Familiar", 1, "", "condición de compra / medio de pago / establecimiento (no evaluable desde el dataset)",
     "El bien debe cumplir reglas de compra/medio de pago/establecimiento definidas por el certificado (no es edad, es condición de compra)"),
]

# ---------------------------------------------------------------------------
# 2. PROPENSION - una tupla por condicion atomica
#    (producto_id, categoria, grupo_and, columna, condicion, texto_original)
# ---------------------------------------------------------------------------
T_DEUDOR = "SI RANGO_SALARIAL sugiere capacidad de endeudamiento (ej. >1.5 SMLV) ENTONCES propensión a Vida Deudor"
T_INCENDIO = "Resuelto (24 jul): SI RANGO_SALARIAL en tier Alto (Entre 8 y 10 SMLV en adelante) ENTONCES propensión a Incendio Deudor"
T_SALUD = "SI DROGUERIA = SI ENTONCES propensión a Póliza de Salud"
T_ASMED = "Resuelto (24 jul): se cae la condición de SEGMENTO_GRUPO_FAMILIAR. Queda solo: SI DROGUERIA = SI ENTONCES propensión a Asistencias médicas familiares — misma condición que SALUD-01, van a empatar cuando ambas apliquen"
T_VIDAAH = "Resuelto (24 jul): SI RANGO_SALARIAL en tier Medio-alto (Entre 4 y 8 SMLV) Y RANGO_EDAD en 36-55 ENTONCES propensión a Vida y Ahorro"
T_ASMULT = "Resuelto (24 jul): SI RANGO_SALARIAL en tier Bajo o Medio (hasta 4 SMLV) ENTONCES propensión a Asistencias múltiples"
T_APEXEQ = "SI RANGO_SALARIAL bajo (Menor al SMLV a 1.5 SMLV) ENTONCES propensión a este producto económico"
T_EXEQ = "SI RANGO_EDAD = \"Mayor de 55 años\" ENTONCES propensión a Exequial"
T_HOGAR = "Resuelto — precedencia explícita (24 jul): SI (RANGO_SALARIAL en tier Medio-alto o Alto Y CIUDAD_AFILIADO no nula) O VIVIENDA = SI ENTONCES propensión a Hogar"
T_ARRENDA = "Resuelto (24 jul): SI RANGO_SALARIAL en tier Bajo o Medio (hasta 4 SMLV) ENTONCES propensión a Seguro de Arrendamiento"
T_MOTO = "Resuelto (24 jul): SI RANGO_SALARIAL en tier Bajo o Medio (hasta 4 SMLV) Y CIUDAD_AFILIADO en municipio periférico (Soacha, Mosquera, Zipaquirá, Funza) ENTONCES propensión a Moto"
T_CARRO = "Resuelto (24 jul): SI RANGO_SALARIAL en tier Medio-alto o Alto (Entre 4 SMLV en adelante — rango extendido a propósito) ENTONCES propensión a Carro"
T_BICI = "SI RANGO_EDAD = \"20 a 35 años\" (proxy débil, sin evidencia fuerte) ENTONCES propensión a Bici/Patineta"

# El orden de esta lista ES el orden de desempate del PASO 2 del motor.
PROPENSION = [
    # --- Crédito ---
    ("DEUDOR-VIDA-01", "Crédito", 1, "RANGO_SALARIAL_LIMPIO", cond(MAYOR_A_1_5), T_DEUDOR),
    # INCENDIO-DEUDOR-01 salio del ranking el 24 jul -> DECLARACION_DIRECTA
    # --- Personal y Familiar ---
    ("SALUD-01", "Personal y Familiar", 1, "DROGUERIA", "SI", T_SALUD),
    ("ASMED-01", "Personal y Familiar", 1, "DROGUERIA", "SI", T_ASMED),
    ("VIDAAH-01", "Personal y Familiar", 1, "RANGO_SALARIAL_LIMPIO", cond(TIER_MEDIO_ALTO), T_VIDAAH),
    ("VIDAAH-01", "Personal y Familiar", 1, "RANGO_EDAD", cond(EDAD_36_55), T_VIDAAH),
    ("ASMULT-01", "Personal y Familiar", 1, "RANGO_SALARIAL_LIMPIO", cond(TIER_BAJO + TIER_MEDIO), T_ASMULT),
    ("APEXEQ-PAL-01", "Personal y Familiar", 1, "RANGO_SALARIAL_LIMPIO", cond(BAJO_EXPLICITO_APEXEQ), T_APEXEQ),
    ("EXEQ-01", "Personal y Familiar", 1, "RANGO_EDAD", "Mayor de 55 años", T_EXEQ),
    # --- Hogar --- (grupo 1 O grupo 2)
    ("HOGAR-01", "Hogar", 1, "RANGO_SALARIAL_LIMPIO", cond(TIER_MEDIO_ALTO + TIER_ALTO), T_HOGAR),
    ("HOGAR-01", "Hogar", 1, "CIUDAD_AFILIADO", "NO_NULO", T_HOGAR),
    ("HOGAR-01", "Hogar", 2, "VIVIENDA", "SI", T_HOGAR),
    ("ARRENDA-01", "Hogar", 1, "RANGO_SALARIAL_LIMPIO", cond(TIER_BAJO + TIER_MEDIO), T_ARRENDA),
    # --- Movilidad ---
    ("MOTO-01", "Movilidad", 1, "RANGO_SALARIAL_LIMPIO", cond(TIER_BAJO + TIER_MEDIO), T_MOTO),
    ("MOTO-01", "Movilidad", 1, "CIUDAD_AFILIADO", cond(CIUDADES_PERIFERICAS), T_MOTO),
    # CARRO-01 salio del ranking el 24 jul -> DECLARACION_DIRECTA
    ("BICI-01", "Movilidad", 1, "RANGO_EDAD", "20 a 35 años", T_BICI),
]

# ---------------------------------------------------------------------------
# 2b. DECLARACION DIRECTA - fuera del ranking de propension (24 jul, 2a ronda)
#     Existen en el catalogo, pero NO compiten por producto_top ni aparecen en
#     productos_alternativos. Solo se ofrecen cuando la persona declara la
#     condicion en conversacion con el bot.
# ---------------------------------------------------------------------------
DECLARACION_DIRECTA = [
    ("INCENDIO-DEUDOR-01", "Crédito",
     "Sale del motor de propension (24 jul): su hipotesis original estaba mal disenada. Pedia salario tier Alto, pero ninguna fila de categoria_top=Credito tiene salario alto, asi que era inalcanzable por construccion."),
    ("CARRO-01", "Movilidad",
     "Sale del motor de propension (24 jul): misma causa que INCENDIO-DEUDOR-01. Pedia salario Medio-alto/Alto, incompatible con que Movilidad gane la categoria. Dejo de ser producto de respaldo de Movilidad."),
    ("AP-CHUBB-01", "Personal y Familiar",
     "Declaracion directa (24 jul): tiene elegibilidad dura verificada pero ninguna hipotesis de propension. Su pendiente_confirmacion_edad se sigue calculando igual."),
    ("APDIG-CHUBB-01", "Personal y Familiar",
     "Declaracion directa (24 jul): idem AP-CHUBB-01."),
    ("ONCO-CHUBB-01", "Personal y Familiar",
     "Declaracion directa (24 jul): idem AP-CHUBB-01."),
    ("URB-CHUBB-01", "Personal y Familiar",
     "Declaracion directa (24 jul): su elegibilidad es condicion de compra, no evaluable desde el dataset."),
    ("DESEMP-01", "Crédito",
     "Declaracion directa: dependia de EMPRESA_FOCO, sin significado confirmado. Sin condicion verificable."),
    ("VIAJE-01", "Personal y Familiar",
     "Declaracion directa: sin columna candidata real. Depende 100% de lo que capture el bot."),
    ("SOAT-01", "Movilidad",
     "Declaracion directa: obligacion legal, solo aplica una vez el bot confirma que la persona tiene vehiculo."),
]
IDS_DECLARACION_DIRECTA = [pid for pid, _, _ in DECLARACION_DIRECTA]

# ---------------------------------------------------------------------------
# 3. SIN HIPOTESIS DE PROPENSION - no se inventa ninguna regla
# ---------------------------------------------------------------------------
SIN_HIPOTESIS = [
    ("VIDA-01", "Personal y Familiar",
     "Reconvertido (24 jul): dependía de SEGMENTO_GRUPO_FAMILIAR sin significado confirmado. Se designa producto general de respaldo de Personal y Familiar."),
    ("PET-SEG-01", "Mascotas",
     "Ninguna columna candidata dentro de nuestra base. Designado producto general de respaldo de Mascotas."),
    ("PET-PREP-01", "Mascotas", "Ninguna columna candidata dentro de nuestra base."),
    ("PET-ASIS-01", "Mascotas", "Ninguna columna candidata dentro de nuestra base."),
]


def main() -> None:
    filas = []
    for pid, cat, grupo, col, condicion, texto in ELEGIBILIDAD_DURA:
        # Los 4 CHUBB conservan su regla de elegibilidad (el motor la usa para
        # pendiente_confirmacion_edad) pero su flujo es declaracion directa.
        filas.append({"producto_id": pid, "categoria": cat, "grupo_and": grupo,
                      "columna_dataset": col, "condicion": condicion,
                      "tipo_regla": "elegibilidad_dura",
                      "flujo": FLUJO_DIRECTO if pid in IDS_DECLARACION_DIRECTA else FLUJO_RANKING,
                      "texto_original": texto})
    for pid, cat, grupo, col, condicion, texto in PROPENSION:
        filas.append({"producto_id": pid, "categoria": cat, "grupo_and": grupo,
                      "columna_dataset": col, "condicion": condicion,
                      "tipo_regla": "propension", "flujo": FLUJO_RANKING,
                      "texto_original": texto})
    # Los de declaracion directa quedan registrados sin condicion operativa:
    # el motor filtra por tipo_regla == "propension", asi que nunca los evalua.
    for pid, cat, motivo in DECLARACION_DIRECTA:
        if pid in {f["producto_id"] for f in filas}:
            continue  # los CHUBB ya entraron con su fila de elegibilidad
        filas.append({"producto_id": pid, "categoria": cat, "grupo_and": "",
                      "columna_dataset": "", "condicion": "",
                      "tipo_regla": "declaracion_directa", "flujo": FLUJO_DIRECTO,
                      "texto_original": motivo})

    with ARCHIVO_SALIDA.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)

    print("=" * 76)
    print("ESTRUCTURACION DE HIPOTESIS v2 - Hipotesis_Generales_Seguros.md (24 jul)")
    print("=" * 76)
    print(f"\nArchivo generado: {ARCHIVO_SALIDA.name}  ({len(filas)} filas de condicion atomica)")

    print("\n--- ESCALA UNICA DE RANGO_SALARIAL_LIMPIO aplicada ---")
    for nombre, tier in [("Bajo", TIER_BAJO), ("Medio", TIER_MEDIO),
                         ("Medio-alto", TIER_MEDIO_ALTO), ("Alto", TIER_ALTO)]:
        print(f"  {nombre:<12} {len(tier)} buckets: {', '.join(tier)}")

    print("\n--- PRODUCTO GENERAL DE RESPALDO por categoria ---")
    for cat, pid in PRODUCTO_RESPALDO.items():
        print(f"  {cat:<22} -> {pid}")

    print("\n--- FILAS POR CATEGORIA Y TIPO ---")
    resumen = {}
    for fila in filas:
        d = resumen.setdefault(fila["categoria"], {"elegibilidad_dura": set(), "propension": set(),
                                                   "declaracion_directa": set(), "filas": 0})
        d[fila["tipo_regla"]].add(fila["producto_id"])
        d["filas"] += 1
    print(f"  {'CATEGORIA':<22} {'PROPENSION':>11} {'ELEGIB.':>9} {'DIRECTA':>9} {'FILAS':>7}")
    print("  " + "-" * 62)
    for cat, d in resumen.items():
        print(f"  {cat:<22} {len(d['propension']):>11} {len(d['elegibilidad_dura']):>9} "
              f"{len(d['declaracion_directa']):>9} {d['filas']:>7}")

    print("\n--- REGLAS DE PROPENSION ESTRUCTURADAS, producto por producto ---")
    por_prod = {}
    for pid, cat, grupo, col, condicion, _ in PROPENSION:
        por_prod.setdefault((pid, cat), []).append((grupo, col, condicion))
    for (pid, cat), conds in por_prod.items():
        grupos = {}
        for g, col, c in conds:
            grupos.setdefault(g, []).append(f"{col} in [{c[:52]}{'...' if len(c) > 52 else ''}]")
        partes = [" Y ".join(v) for v in grupos.values()]
        print(f"  {pid:<20} ({cat})")
        print(f"      {' O '.join(partes)}")

    print("\n" + "=" * 76)
    print(f"DECLARACION DIRECTA - {len(DECLARACION_DIRECTA)} productos FUERA del ranking")
    print("=" * 76)
    print("No compiten por producto_top ni aparecen en productos_alternativos.\n")
    for pid, cat, motivo in DECLARACION_DIRECTA:
        print(f"  {pid:<20} ({cat:<20})")
        print(f"      {motivo[:104]}")

    print("\n" + "!" * 76)
    print(f"AVISO - {len(SIN_HIPOTESIS)} PRODUCTOS SIN HIPOTESIS, PERO DENTRO DEL FLUJO")
    print("!" * 76)
    print("No se invento ninguna regla. Solo llegan a producto_top via respaldo.\n")
    for pid, cat, motivo in SIN_HIPOTESIS:
        respaldo = "  <-- es producto de respaldo" if PRODUCTO_RESPALDO.get(cat) == pid else ""
        print(f"  {pid:<18} ({cat:<20}){respaldo}")
        print(f"      {motivo[:100]}")

    print("\n" + "=" * 76)
    print("COBERTURA DE LOS 24 PRODUCTOS DEL CATALOGO")
    print("=" * 76)
    con_prop = {p for p, _, _, _, _, _ in PROPENSION}
    con_eleg = {p for p, _, _, _, _, _ in ELEGIBILIDAD_DURA}
    sin_hip = {p for p, _, _ in SIN_HIPOTESIS}
    directa = set(IDS_DECLARACION_DIRECTA)
    print(f"  Compiten en el ranking, con hipotesis : {len(con_prop):>3}")
    print(f"  Compiten, sin hipotesis (solo respaldo): {len(sin_hip):>3}")
    print(f"  Declaracion directa (fuera del ranking): {len(directa):>3}")
    print(f"  {'-' * 44}")
    print(f"  TOTAL productos distintos             : {len(con_prop | con_eleg | sin_hip | directa):>3}")
    solapan = con_prop & directa
    print(f"  Solapamiento ranking/directa (debe ser 0): {sorted(solapan) if solapan else 'ninguno - OK'}")

    # Contraste contra el catalogo real, para detectar desalineaciones de id.
    catalogo = BASE / "data" / "catalogo" / "catalogo_productos.csv"
    if catalogo.exists():
        with catalogo.open(encoding="utf-8") as f:
            ids_cat = {r["producto_id"] for r in csv.DictReader(f)}
        ids_hip = con_prop | con_eleg | sin_hip | directa
        print(f"\n  Productos en catalogo_productos.csv : {len(ids_cat)}")
        faltan = ids_cat - ids_hip
        sobran = ids_hip - ids_cat
        print(f"  En el catalogo pero no en hipotesis : {sorted(faltan) if faltan else 'ninguno - OK'}")
        print(f"  En hipotesis pero no en el catalogo : {sorted(sobran) if sobran else 'ninguno - OK'}")

    print("\n*** APEXEQ-PAL-01 - RESUELTO (24 jul, 2a ronda) ***")
    print("  Respeta su parentesis original: 'Menor al SMLV a 1.5 SMLV' = 2 buckets.")
    print("  NO se expande a los 3 del tier Bajo.")
    print("  Regla general: la escala unica solo aplica a terminos que no traian ya")
    print("  su propio alcance explicito por escrito.")


if __name__ == "__main__":
    main()

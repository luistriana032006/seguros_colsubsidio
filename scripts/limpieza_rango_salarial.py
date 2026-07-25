"""
Limpieza quirurgica de UNA sola columna: RANGO_SALARIAL.

POR QUE SOLO ESTA COLUMNA Y NINGUNA OTRA
----------------------------------------
Tras explorar el dataset completo ya se decidio que la mayoria de los
"problemas" del archivo no son errores a corregir:

  - PISCILAGO es constante -> se excluye del modelo, no se limpia.
  - HOTELES / AGENCIAS / VIVIENDA tienen activacion casi nula -> es dato
    real, solo raro. No se "corrige".
  - Los ~15.560 grupos de filas "duplicadas" NO son duplicados: son
    personas distintas que comparten valores en columnas de baja
    cardinalidad. NO se aplica deduplicacion bajo ningun criterio.
  - Los codigos griegos de CATEGORIA / SEGMENTO_* / PIRAMIDE_NUEVA son
    anonimizacion intencional confirmada por negocio, no un error.

RANGO_SALARIAL es la unica columna con un problema real: conviven dos
esquemas de bucketing distintos (uno fino y dominante, uno grueso y
minoritario). Este script remapea el minoritario al dominante y
recategoriza los nulos como "Desconocido".

REGLAS DE ESTE SCRIPT
---------------------
  - No borra ninguna fila. Entran 500.000, salen 500.000.
  - No sobrescribe la columna original: crea RANGO_SALARIAL_LIMPIO al lado.
  - No toca ninguna otra columna.
  - No escribe sobre el Excel original: genera un archivo nuevo.

Uso:  python3 limpieza_rango_salarial.py
"""

from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent  # raiz del repo (este script vive en scripts/)
ARCHIVO_ENTRADA = BASE / "data" / "raw" / "Usos_Productos_Afiliados_SIN_ID.xlsx"
ARCHIVO_SALIDA = BASE / "data" / "processed" / "Usos_Productos_Afiliados_RANGO_SALARIAL_LIMPIO.csv"

COLUMNA_ORIGINAL = "RANGO_SALARIAL"
COLUMNA_LIMPIA = "RANGO_SALARIAL_LIMPIO"
ETIQUETA_NULO = "Desconocido"

# Esquema dominante (fino): el que usa la practica totalidad de las filas.
# Se lista en orden de ingreso para poder ordenar reportes de forma legible.
ESQUEMA_DOMINANTE = [
    "Menor al SMLV",
    "Entre 1 y 1.5 SMLV",
    "Entre 1.5 y 2 SMLV",
    "Entre 2 y 2.5 SMLV",
    "Entre 2.5 y 3 SMLV",
    "Entre 3 y 4 SMLV",
    "Entre 4 y 6 SMLV",
    "Entre 6 y 8 SMLV",
    "Entre 8 y 10 SMLV",
    "Entre 10 y 20 SMLV",
    "Entre 20 y 30 SMLV",
    "Mayor a 30 SMLV",
]

# Tabla de equivalencia esquema minoritario -> esquema dominante.
# Criterio unico y uniforme: cada bucket grueso se solapa con varios buckets
# finos; se elige el bucket fino que concentra MAS poblacion dentro de ese
# solape (asignacion de maxima verosimilitud). El razonamiento fila por fila
# esta documentado en apuntes/decisiones_limpieza_rango_salarial.md.
MAPA_REMAPEO = {
    "Menor a 2 SMLV": "Entre 1 y 1.5 SMLV",
    "Entre 2 y 4 SMLV": "Entre 2 y 2.5 SMLV",
    "Entre 4 y 8 SMLV": "Entre 4 y 6 SMLV",
    "Entre 8 y 19 SMLV": "Entre 10 y 20 SMLV",
}


def diagnostico(serie: pd.Series) -> None:
    """PASO 1 - imprime el estado de la columna ANTES de tocar nada."""
    print("=" * 72)
    print("PASO 1 - DIAGNOSTICO DE RANGO_SALARIAL (antes de cambiar nada)")
    print("=" * 72)

    conteo = serie.value_counts(dropna=False)
    total = len(serie)
    print(f"\nValores unicos (incluyendo nulos): {len(conteo)}")
    print(f"{'VALOR':<24} {'FILAS':>8} {'%':>8}   ESQUEMA")
    print("-" * 72)
    for valor, n in conteo.items():
        if pd.isna(valor):
            etiqueta, esquema = "(nulo)", "nulo"
        else:
            etiqueta = valor
            esquema = "minoritario" if valor in MAPA_REMAPEO else "dominante"
        print(f"{etiqueta:<24} {n:>8,} {n / total:>7.3%}   {esquema}")

    n_dominante = serie.isin(ESQUEMA_DOMINANTE).sum()
    n_minoritario = serie.isin(MAPA_REMAPEO).sum()
    n_nulos = serie.isna().sum()

    print("-" * 72)
    print(f"Esquema DOMINANTE (fino) : {n_dominante:>8,} filas ({n_dominante / total:.3%})")
    print(f"Esquema MINORITARIO      : {n_minoritario:>8,} filas ({n_minoritario / total:.3%})")
    print(f"Nulos                    : {n_nulos:>8,} filas ({n_nulos / total:.3%})")

    # Cualquier valor que no encaje en ninguno de los dos esquemas conocidos
    # es una sorpresa: se avisa fuerte en vez de dejarlo pasar en silencio.
    conocidos = set(ESQUEMA_DOMINANTE) | set(MAPA_REMAPEO)
    inesperados = set(serie.dropna().unique()) - conocidos
    if inesperados:
        print("\n*** ATENCION: valores no contemplados por este script ***")
        for valor in sorted(inesperados):
            print(f"    - {valor!r}")
        print("    Quedan intactos en la columna limpia. Revisar antes de usar el archivo.")
    else:
        print("\nSin valores inesperados: todo cae en uno de los dos esquemas o es nulo.")


def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """PASOS 2, 3 y 4 - remapeo, nulos a 'Desconocido' y columna nueva al lado."""
    print("\n" + "=" * 72)
    print("PASOS 2-4 - REMAPEO, NULOS Y TRAZABILIDAD")
    print("=" * 72)

    original = df[COLUMNA_ORIGINAL]

    # PASO 2: remapeo, NO borrado. Los valores del esquema dominante pasan
    # tal cual; solo cambian los 4 valores del esquema minoritario.
    limpia = original.replace(MAPA_REMAPEO)

    # PASO 3: los nulos se recategorizan, la fila nunca se elimina.
    limpia = limpia.fillna(ETIQUETA_NULO)

    # PASO 4: columna nueva al lado de la original, no encima de ella.
    posicion = df.columns.get_loc(COLUMNA_ORIGINAL) + 1
    df.insert(posicion, COLUMNA_LIMPIA, limpia)

    print(f"\nColumna '{COLUMNA_LIMPIA}' insertada justo despues de '{COLUMNA_ORIGINAL}'.")
    print("Remapeos aplicados:")
    for origen, destino in MAPA_REMAPEO.items():
        n = (original == origen).sum()
        print(f"  {origen:<22} -> {destino:<22} ({n:>4,} filas)")
    print(f"  {'(nulo)':<22} -> {ETIQUETA_NULO:<22} ({original.isna().sum():>4,} filas)")

    return df


def verificacion(df: pd.DataFrame, filas_esperadas: int) -> bool:
    """PASO 5 - cuenta que cambio, que quedo Desconocido y que no se perdio nada."""
    print("\n" + "=" * 72)
    print("PASO 5 - VERIFICACION")
    print("=" * 72)

    original = df[COLUMNA_ORIGINAL]
    limpia = df[COLUMNA_LIMPIA]

    n_remapeadas = original.isin(MAPA_REMAPEO).sum()
    n_desconocido = (limpia == ETIQUETA_NULO).sum()
    n_intactas = len(df) - n_remapeadas - n_desconocido

    print(f"\nFilas que cambiaron de valor (remapeo de esquema) : {n_remapeadas:,}")
    print(f"Filas que quedaron como '{ETIQUETA_NULO}'              : {n_desconocido:,}")
    print(f"Filas que quedaron identicas a la original        : {n_intactas:,}")

    ok_filas = len(df) == filas_esperadas
    print(f"\nFilas de entrada : {filas_esperadas:,}")
    print(f"Filas de salida  : {len(df):,}")
    print(f"Integridad de filas: {'OK - no se perdio ninguna fila' if ok_filas else 'ERROR - CAMBIO EL NUMERO DE FILAS'}")

    # La columna original debe seguir exactamente igual que en el Excel.
    ok_original = original.value_counts(dropna=False).equals(
        pd.read_excel(ARCHIVO_ENTRADA, usecols=[COLUMNA_ORIGINAL])[COLUMNA_ORIGINAL].value_counts(dropna=False)
    )
    print(f"Columna original intacta: {'OK' if ok_original else 'ERROR - la original fue modificada'}")

    # Ya no debe quedar ningun valor del esquema minoritario ni ningun nulo.
    ok_esquema = not limpia.isin(MAPA_REMAPEO).any()
    ok_nulos = not limpia.isna().any()
    print(f"Esquema minoritario eliminado de la columna limpia: {'OK' if ok_esquema else 'ERROR'}")
    print(f"Sin nulos en la columna limpia: {'OK' if ok_nulos else 'ERROR'}")

    print("\nDistribucion final de RANGO_SALARIAL_LIMPIO:")
    orden = ESQUEMA_DOMINANTE + [ETIQUETA_NULO]
    conteo = limpia.value_counts()
    for valor in orden:
        if valor in conteo:
            print(f"  {valor:<24} {conteo[valor]:>8,}  ({conteo[valor] / len(df):.3%})")

    return ok_filas and ok_original and ok_esquema and ok_nulos


def main() -> None:
    print(f"Leyendo {ARCHIVO_ENTRADA.name} ...")
    df = pd.read_excel(ARCHIVO_ENTRADA)
    filas_esperadas = len(df)

    diagnostico(df[COLUMNA_ORIGINAL])
    df = limpiar(df)
    todo_ok = verificacion(df, filas_esperadas)

    df.to_csv(ARCHIVO_SALIDA, index=False, encoding="utf-8")
    print(f"\nArchivo generado: {ARCHIVO_SALIDA.name} ({ARCHIVO_SALIDA.stat().st_size / 1e6:.1f} MB)")
    print(f"El original '{ARCHIVO_ENTRADA.name}' NO fue modificado.")
    print("\nRESULTADO:", "TODAS LAS VERIFICACIONES PASARON" if todo_ok else "*** HAY VERIFICACIONES EN ERROR - REVISAR ***")


if __name__ == "__main__":
    main()

"""Genera 5.000 perfiles sintéticos de usuarios y los guarda en data/sintetico/datos_sinteticos.csv.

Franjas (ver apuntes/Hipotesis_Generales_Seguros.md para las hipótesis fuente):
- 70% (3.500): perfil construido para cumplir una hipótesis puntual -> producto de esa hipótesis.
- 20% (1.000): perfil con señales mixtas (sin construir a propósito) -> producto de respaldo de una categoría.
- 10% (500): perfil aleatorio -> producto elegido al azar entre los productos elegibles, sin relación con el perfil.

Nota: varias hipótesis comparten condición de disparo (p. ej. ASMULT-01 y ARRENDA-01 usan el
mismo rango salarial bajo/medio). Cuando la franja de hipótesis construye un perfil para una de
ellas, es normal que la condición de otra también quede satisfecha por construcción — no es un
error de generación, es un solapamiento real de las hipótesis del documento fuente.
"""
import random
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CATALOGO = RAIZ / "data" / "catalogo" / "catalogo_productos.csv"
RUTA_SALIDA = RAIZ / "data" / "sintetico" / "datos_sinteticos.csv"

N_HIPOTESIS = 3500
N_MIXTO = 1000
N_RUIDO = 500
N_TOTAL = N_HIPOTESIS + N_MIXTO + N_RUIDO

CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga",
            "Soacha", "Mosquera", "Zipaquirá", "Funza", "Manizales"]
PESOS_CIUDAD = [0.40, 0.20, 0.10, 0.08, 0.07, 0.05, 0.03, 0.03, 0.02, 0.02]
MUNICIPIOS_PERIFERICOS = ["Soacha", "Mosquera", "Zipaquirá", "Funza"]

TIPOS_DOCUMENTO = ["CC", "CE", "PA"]
PESOS_TIPO_DOCUMENTO = [0.90, 0.07, 0.03]

RANGOS_SALARIALES = ["menor_smlv", "1_1.5", "1.5_2", "2_2.5", "2.5_3", "3_4",
                      "4_6", "6_8", "8_10", "10_20", "20_30", "mayor_30"]
RANGOS_BAJO_MEDIO = ["menor_smlv", "1_1.5", "1.5_2", "2_2.5", "2.5_3", "3_4"]
RANGOS_MEDIO_ALTO_ALTO = ["4_6", "6_8", "8_10", "10_20", "20_30", "mayor_30"]

TIPOS_VIVIENDA = ["propia", "arrendada", "familiar"]
ESTADOS_CIVILES = ["soltero", "casado", "union_libre", "divorciado", "viudo"]

TIPOS_VEHICULO = ["carro", "moto", "bici", "ninguno"]
PESOS_TIPO_VEHICULO = [0.25, 0.25, 0.10, 0.40]

TIPOS_MASCOTA = ["perro", "gato", "otro"]
PESOS_TIPO_MASCOTA = [0.60, 0.25, 0.15]

# Tasas base sin cifra oficial en las fuentes leídas (apuntes/Hipotesis_Generales_Seguros.md,
# catalogo_productos.csv) -> supuestos razonables para la demo, documentados aquí.
P_TIENE_DEPENDIENTES = 0.45
P_USA_DROGUERIA_BASE = 0.25
P_USA_HOTELES = 0.03   # tope duro del enunciado: máximo 5% de activación
P_USA_AGENCIAS = 0.02  # tope duro del enunciado: máximo 3% de activación
P_TIENE_MASCOTA_BASE = 0.67  # DANE, Encuesta Multipropósito 2021 (Fuente 3 del .md)

NOMBRES = ["carlos", "maria", "juan", "ana", "luis", "sofia", "andres", "laura",
           "diego", "camila", "jorge", "paula", "felipe", "valentina", "santiago",
           "daniela", "sebastian", "natalia", "david", "carolina", "julian", "diana"]
APELLIDOS = ["gomez", "rodriguez", "martinez", "lopez", "garcia", "perez", "gonzalez",
             "sanchez", "ramirez", "torres", "florez", "castro", "vargas", "moreno",
             "rojas", "suarez", "jimenez", "ortiz"]
DOMINIOS_CORREO = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com"]

PRODUCTOS_EXCLUIDOS = {
    "INCENDIO-DEUDOR-01", "CARRO-01", "AP-CHUBB-01", "APDIG-CHUBB-01",
    "ONCO-CHUBB-01", "URB-CHUBB-01", "DESEMP-01", "SOAT-01", "VIAJE-01",
}

RESPALDO_POR_CATEGORIA = {
    "Crédito": "DEUDOR-VIDA-01",
    "Personal y Familiar": "VIDA-01",
    "Hogar": "HOGAR-01",
    "Movilidad": "BICI-01",
    "Mascotas": "PET-SEG-01",
}

COLUMNAS = ["id_interno", "id_contacto", "edad", "ciudad", "tipo_documento",
            "rango_salarial", "tipo_vivienda", "tiene_dependientes",
            "num_dependientes", "estado_civil", "usa_drogueria", "usa_hoteles",
            "usa_agencias", "tiene_mascota", "tipo_mascota", "tipo_vehiculo",
            "producto_comprado"]

COLUMNAS_BOOLEANAS = ["tiene_dependientes", "usa_drogueria", "usa_hoteles",
                       "usa_agencias", "tiene_mascota"]


def cargar_productos_elegibles():
    catalogo = pd.read_csv(RUTA_CATALOGO)
    todos = set(catalogo["producto_id"])
    faltantes = PRODUCTOS_EXCLUIDOS - todos
    if faltantes:
        raise ValueError(f"Productos excluidos que no existen en el catálogo: {sorted(faltantes)}")
    return sorted(todos - PRODUCTOS_EXCLUIDOS)


def elegir_ciudad():
    return str(np.random.choice(CIUDADES, p=PESOS_CIUDAD))


def elegir_tipo_documento():
    return str(np.random.choice(TIPOS_DOCUMENTO, p=PESOS_TIPO_DOCUMENTO))


def elegir_tipo_mascota():
    return str(np.random.choice(TIPOS_MASCOTA, p=PESOS_TIPO_MASCOTA))


def generar_id_contacto():
    r = random.random()
    if r < 0.60:
        return "3" + "".join(str(random.randint(0, 9)) for _ in range(9))
    if r < 0.90:
        nombre = random.choice(NOMBRES)
        apellido = random.choice(APELLIDOS)
        dominio = random.choice(DOMINIOS_CORREO)
        return f"{nombre}.{apellido}{random.randint(1, 99)}@{dominio}"
    return None


def generar_perfil_base():
    tiene_dependientes = random.random() < P_TIENE_DEPENDIENTES
    tiene_mascota = random.random() < P_TIENE_MASCOTA_BASE
    return {
        "id_interno": str(uuid.uuid4()),
        "id_contacto": generar_id_contacto(),
        "edad": random.randint(18, 75),
        "ciudad": elegir_ciudad(),
        "tipo_documento": elegir_tipo_documento(),
        "rango_salarial": random.choice(RANGOS_SALARIALES),
        "tipo_vivienda": random.choice(TIPOS_VIVIENDA),
        "tiene_dependientes": tiene_dependientes,
        "num_dependientes": random.randint(1, 4) if tiene_dependientes else 0,
        "estado_civil": random.choice(ESTADOS_CIVILES),
        "usa_drogueria": random.random() < P_USA_DROGUERIA_BASE,
        "usa_hoteles": random.random() < P_USA_HOTELES,
        "usa_agencias": random.random() < P_USA_AGENCIAS,
        "tiene_mascota": tiene_mascota,
        "tipo_mascota": elegir_tipo_mascota() if tiene_mascota else None,
        "tipo_vehiculo": str(np.random.choice(TIPOS_VEHICULO, p=PESOS_TIPO_VEHICULO)),
    }


# --- Generadores de hipótesis (franja 70%) ---
# Cada uno fuerza en el perfil los campos que su hipótesis exige y devuelve el producto_comprado.

def _hip_salud(perfil):
    perfil["usa_drogueria"] = True
    return random.choice(["SALUD-01", "ASMED-01"])


def _hip_vidaah(perfil):
    perfil["rango_salarial"] = random.choice(["4_6", "6_8"])
    perfil["edad"] = random.randint(36, 55)
    return "VIDAAH-01"


def _hip_apexeq(perfil):
    perfil["rango_salarial"] = random.choice(["menor_smlv", "1_1.5"])
    return "APEXEQ-PAL-01"


def _hip_exeq(perfil):
    perfil["edad"] = random.randint(55, 75)
    return "EXEQ-01"


def _hip_asmult(perfil):
    perfil["rango_salarial"] = random.choice(RANGOS_BAJO_MEDIO)
    return "ASMULT-01"


def _hip_hogar(perfil):
    perfil["rango_salarial"] = random.choice(RANGOS_MEDIO_ALTO_ALTO)
    # ciudad nunca es null por construcción del perfil base -> condición ya satisfecha
    return "HOGAR-01"


def _hip_arrenda(perfil):
    perfil["rango_salarial"] = random.choice(RANGOS_BAJO_MEDIO)
    return "ARRENDA-01"


def _hip_moto(perfil):
    perfil["rango_salarial"] = random.choice(RANGOS_BAJO_MEDIO)
    perfil["ciudad"] = random.choice(MUNICIPIOS_PERIFERICOS)
    return "MOTO-01"


def _hip_bici(perfil):
    perfil["edad"] = random.randint(20, 35)
    return "BICI-01"


def _hip_mascotas(perfil):
    perfil["tiene_mascota"] = True
    perfil["tipo_mascota"] = elegir_tipo_mascota()
    return random.choice(["PET-SEG-01", "PET-PREP-01", "PET-ASIS-01"])


def _hip_deudor(perfil):
    perfil["rango_salarial"] = random.choice(["1_1.5", "1.5_2", "2_2.5", "2.5_3", "3_4", "4_6"])
    return "DEUDOR-VIDA-01"


GENERADORES_HIPOTESIS = [
    _hip_salud, _hip_vidaah, _hip_apexeq, _hip_exeq, _hip_asmult,
    _hip_hogar, _hip_arrenda, _hip_moto, _hip_bici, _hip_mascotas, _hip_deudor,
]


def generar_filas(productos_elegibles):
    filas = []
    franjas = []

    for _ in range(N_HIPOTESIS):
        perfil = generar_perfil_base()
        generador = random.choice(GENERADORES_HIPOTESIS)
        perfil["producto_comprado"] = generador(perfil)
        filas.append(perfil)
        franjas.append("hipotesis")

    for _ in range(N_MIXTO):
        perfil = generar_perfil_base()
        categoria = random.choice(list(RESPALDO_POR_CATEGORIA.keys()))
        perfil["producto_comprado"] = RESPALDO_POR_CATEGORIA[categoria]
        filas.append(perfil)
        franjas.append("mixto")

    for _ in range(N_RUIDO):
        perfil = generar_perfil_base()
        perfil["producto_comprado"] = random.choice(productos_elegibles)
        filas.append(perfil)
        franjas.append("ruido")

    combinado = list(zip(filas, franjas))
    random.shuffle(combinado)
    filas, franjas = zip(*combinado)
    return list(filas), list(franjas)


def verificar(df, franjas):
    errores = []

    nulos_producto = df["producto_comprado"].isna().sum()
    if nulos_producto > 0:
        errores.append(f"{nulos_producto} filas con producto_comprado nulo")

    excluidos_presentes = set(df["producto_comprado"].dropna()) & PRODUCTOS_EXCLUIDOS
    if excluidos_presentes:
        errores.append(f"productos excluidos presentes en producto_comprado: {sorted(excluidos_presentes)}")

    conteo_franjas = pd.Series(franjas).value_counts()
    total = len(franjas)
    objetivos = {"hipotesis": 0.70, "mixto": 0.20, "ruido": 0.10}
    for franja, objetivo in objetivos.items():
        real = conteo_franjas.get(franja, 0) / total
        if abs(real - objetivo) > 0.02:
            errores.append(
                f"franja '{franja}': {real:.2%} obtenido vs {objetivo:.0%} esperado (fuera de ±2%)"
            )

    if errores:
        raise ValueError("Verificación de datos sintéticos falló:\n- " + "\n- ".join(errores))


def main():
    productos_elegibles = cargar_productos_elegibles()

    filas, franjas = generar_filas(productos_elegibles)
    df = pd.DataFrame(filas, columns=COLUMNAS)

    print(f"Total de filas generadas: {len(df)}")
    print()
    print("Distribución de producto_comprado:")
    print(df["producto_comprado"].value_counts().to_string())
    print()

    conteo_franjas = pd.Series(franjas).value_counts()
    print("Distribución de las tres franjas:")
    for franja, n_esperado in [("hipotesis", N_HIPOTESIS), ("mixto", N_MIXTO), ("ruido", N_RUIDO)]:
        n = conteo_franjas.get(franja, 0)
        print(f"  {franja}: {n} filas ({n / len(df):.1%}) — esperado {n_esperado}")
    print()

    tasa_hoteles = df["usa_hoteles"].mean()
    tasa_agencias = df["usa_agencias"].mean()
    if tasa_hoteles > 0.05:
        print(f"ADVERTENCIA: usa_hoteles activado en {tasa_hoteles:.2%} de filas (tope 5%)")
    if tasa_agencias > 0.03:
        print(f"ADVERTENCIA: usa_agencias activado en {tasa_agencias:.2%} de filas (tope 3%)")

    verificar(df, franjas)
    print("Todas las verificaciones pasaron.")

    df_salida = df.copy()
    for columna in COLUMNAS_BOOLEANAS:
        df_salida[columna] = df_salida[columna].map({True: "true", False: "false"})

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df_salida.to_csv(RUTA_SALIDA, index=False, sep=",", encoding="utf-8")
    print(f"Guardado en {RUTA_SALIDA}")


if __name__ == "__main__":
    main()

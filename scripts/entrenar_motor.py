"""Calcula el peso real de cada hipótesis combinando datos sintéticos y datos
reales, y lo guarda en data/modelos/pesos_hipotesis.json.

Dos fuentes:
- data/sintetico/datos_sinteticos.csv: los 5.000 perfiles base.
- data/motor.db (usuarios JOIN recomendaciones): perfiles reales que ya pasaron
  por motor.recomendar() + motor.registrar() -- vía server.py, mcp_server.py o
  app.py. Cuentan 3x en la fórmula (FACTOR_PESO_REAL) porque son comportamiento
  real, no generado.

peso = (soporte_sintetico + soporte_real * 3) / (total_sintetico + total_real * 3)

soporte/total_producto en el JSON de salida quedan como conteos reales (sin el
factor 3) -- ese factor solo entra en el cálculo del peso, no se mezcla con
"cuántos registros hay" para no inflar un número que se lee como conteo literal.

Antes de calcular nada, si ya existe un pesos_hipotesis.json de una corrida
anterior, se copia a pesos_hipotesis_anterior.json (para que dashboard_pesos.py
pueda comparar antes/después).
"""
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RUTA_DATOS_SINTETICOS = RAIZ / "data" / "sintetico" / "datos_sinteticos.csv"
RUTA_DB = RAIZ / "data" / "motor.db"
RUTA_SALIDA = RAIZ / "data" / "modelos" / "pesos_hipotesis.json"
RUTA_SALIDA_ANTERIOR = RAIZ / "data" / "modelos" / "pesos_hipotesis_anterior.json"

FLOOR_MINIMO = 0.05
PESO_SIN_DATOS = 0.01
FACTOR_PESO_REAL = 3

COLUMNAS_PERFIL_REAL = [
    "edad", "ciudad", "rango_salarial", "tipo_vivienda", "tiene_dependientes",
    "num_dependientes", "estado_civil", "usa_drogueria", "usa_hoteles",
    "usa_agencias", "tiene_mascota", "tipo_mascota", "tipo_vehiculo",
]
COLUMNAS_BOOLEANAS = ["tiene_dependientes", "usa_drogueria", "usa_hoteles", "usa_agencias", "tiene_mascota"]

HIPOTESIS_A_CALCULAR = {
    "salud": {
        "drogueria_activa": {
            "condicion": "usa_drogueria == True",
            "productos": ["SALUD-01", "ASMED-01"],
        },
        "tiene_dependientes_salud": {
            "condicion": "tiene_dependientes == True",
            "productos": ["ASMED-01"],
        },
    },
    "familia": {
        "ahorro_mediano_plazo": {
            "condicion": "rango_salarial in ['4_6','6_8'] and edad >= 36 and edad <= 55",
            "productos": ["VIDAAH-01"],
        },
        "salario_bajo_familia": {
            "condicion": "rango_salarial in ['menor_smlv','1_1.5']",
            "productos": ["APEXEQ-PAL-01"],
        },
        "mayor_55": {
            "condicion": "edad >= 55",
            "productos": ["EXEQ-01"],
        },
        "salario_bajo_medio_familia": {
            "condicion": "rango_salarial in ['menor_smlv','1_1.5','1.5_2','2_2.5','2.5_3','3_4']",
            "productos": ["ASMULT-01"],
        },
        "tiene_dependientes_familia": {
            "condicion": "tiene_dependientes == True",
            "productos": ["VIDA-01"],
        },
    },
    "hogar": {
        "salario_alto_hogar": {
            "condicion": "rango_salarial in ['4_6','6_8','8_10','10_20','20_30','mayor_30']",
            "productos": ["HOGAR-01"],
        },
        "salario_bajo_medio_hogar": {
            "condicion": "rango_salarial in ['menor_smlv','1_1.5','1.5_2','2_2.5','2.5_3','3_4']",
            "productos": ["ARRENDA-01"],
        },
        "vivienda_propia": {
            "condicion": "tipo_vivienda == 'propia'",
            "productos": ["HOGAR-01"],
        },
    },
    "movilidad": {
        "periferia_salario_bajo": {
            "condicion": (
                "rango_salarial in ['menor_smlv','1_1.5','1.5_2','2_2.5','2.5_3','3_4'] "
                "and ciudad in ['Soacha','Mosquera','Zipaquirá','Funza']"
            ),
            "productos": ["MOTO-01"],
        },
        "edad_joven_bici": {
            "condicion": "edad >= 20 and edad <= 35",
            "productos": ["BICI-01"],
        },
        "vehiculo_moto": {
            "condicion": "tipo_vehiculo == 'moto'",
            "productos": ["MOTO-01"],
        },
        "vehiculo_bici": {
            "condicion": "tipo_vehiculo == 'bici'",
            "productos": ["BICI-01"],
        },
    },
    "mascotas": {
        "tiene_mascota": {
            "condicion": "tiene_mascota == True",
            "productos": ["PET-SEG-01"],
        },
        "salario_bajo_medio_mascota": {
            "condicion": "rango_salarial in ['menor_smlv','1_1.5','1.5_2','2_2.5','2.5_3','3_4']",
            "productos": ["PET-PREP-01"],
        },
        "bucaramanga_mascota": {
            "condicion": "ciudad == 'Bucaramanga'",
            "productos": ["PET-SEG-01"],
            "ajuste": -0.2,
        },
    },
    "credito": {
        "salario_medio_bajo_credito": {
            "condicion": "rango_salarial in ['1_1.5','1.5_2','2_2.5','2.5_3','3_4','4_6']",
            "productos": ["DEUDOR-VIDA-01"],
        },
    },
}


def _respaldar_pesos_anteriores():
    """CAMBIO 1: si ya hay un pesos_hipotesis.json, lo copia antes de sobreescribirlo."""
    if RUTA_SALIDA.exists():
        shutil.copy2(RUTA_SALIDA, RUTA_SALIDA_ANTERIOR)
        return True
    return False


def _cargar_datos_reales():
    """CAMBIO 2: usuarios JOIN recomendaciones con producto_principal no nulo,
    convertido al mismo formato de columnas que el CSV sintético. DataFrame
    vacío (no excepción) si la DB, las tablas, o filas todavía no existen."""
    columnas_vacias = COLUMNAS_PERFIL_REAL + ["producto_comprado"]
    if not RUTA_DB.exists():
        return pd.DataFrame(columns=columnas_vacias)

    conexion = sqlite3.connect(RUTA_DB)
    try:
        tablas = {
            fila[0] for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if not {"usuarios", "recomendaciones"}.issubset(tablas):
            return pd.DataFrame(columns=columnas_vacias)

        df_real = pd.read_sql_query(
            """
            SELECT u.edad, u.ciudad, u.rango_salarial, u.tipo_vivienda, u.tiene_dependientes,
                   u.num_dependientes, u.estado_civil, u.usa_drogueria, u.usa_hoteles,
                   u.usa_agencias, u.tiene_mascota, u.tipo_mascota, u.tipo_vehiculo,
                   r.producto_principal AS producto_comprado
            FROM usuarios u
            JOIN recomendaciones r ON r.usuario_id = u.id
            WHERE r.producto_principal IS NOT NULL
            """,
            conexion,
        )
    finally:
        conexion.close()

    for columna in COLUMNAS_BOOLEANAS:
        df_real[columna] = df_real[columna].astype(bool)

    return df_real


def _calcular_peso(df_sintetico, df_real, condicion, productos, ajuste=None):
    """CAMBIO 3: combina soporte/total de ambas fuentes, con los reales pesando FACTOR_PESO_REAL."""
    mascara_producto_sint = df_sintetico["producto_comprado"].isin(productos)
    total_sintetico = int(mascara_producto_sint.sum())
    mascara_condicion_sint = df_sintetico.eval(condicion, engine="python")
    soporte_sintetico = int((mascara_condicion_sint & mascara_producto_sint).sum())

    if len(df_real) > 0:
        mascara_producto_real = df_real["producto_comprado"].isin(productos)
        total_real = int(mascara_producto_real.sum())
        mascara_condicion_real = df_real.eval(condicion, engine="python")
        soporte_real = int((mascara_condicion_real & mascara_producto_real).sum())
    else:
        total_real = 0
        soporte_real = 0

    soporte_ponderado = soporte_sintetico + soporte_real * FACTOR_PESO_REAL
    total_ponderado = total_sintetico + total_real * FACTOR_PESO_REAL

    if total_ponderado == 0:
        peso = PESO_SIN_DATOS
    else:
        peso = soporte_ponderado / total_ponderado
        if peso < FLOOR_MINIMO:
            peso = FLOOR_MINIMO

    if ajuste is not None:
        peso += ajuste

    soporte_total = soporte_sintetico + soporte_real
    total_producto = total_sintetico + total_real
    return round(peso, 4), soporte_total, total_producto


def entrenar():
    hubo_anterior = _respaldar_pesos_anteriores()

    df_sintetico = pd.read_csv(RUTA_DATOS_SINTETICOS)
    df_real = _cargar_datos_reales()

    pesos = {}
    for necesidad, hipotesis_necesidad in HIPOTESIS_A_CALCULAR.items():
        pesos[necesidad] = {}
        for clave, definicion in hipotesis_necesidad.items():
            peso, soporte, total_producto = _calcular_peso(
                df_sintetico, df_real, definicion["condicion"], definicion["productos"], definicion.get("ajuste")
            )
            pesos[necesidad][clave] = {
                "peso": peso,
                "productos": definicion["productos"],
                "soporte": soporte,
                "total_producto": total_producto,
            }

    registros_sinteticos = len(df_sintetico)
    registros_reales = len(df_real)

    salida = {
        "version": "v2",
        "fecha_entrenamiento": datetime.now(timezone.utc).isoformat(),
        "total_registros_entrenamiento": registros_sinteticos + registros_reales,
        "registros_sinteticos": registros_sinteticos,
        "registros_reales": registros_reales,
        "factor_peso_real": FACTOR_PESO_REAL,
        "pesos": pesos,
    }

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(RUTA_SALIDA, "w", encoding="utf-8") as archivo:
        json.dump(salida, archivo, ensure_ascii=False, indent=2)

    return salida, hubo_anterior


if __name__ == "__main__":
    resultado, hubo_anterior = entrenar()

    filas = []
    for necesidad, hipotesis_necesidad in resultado["pesos"].items():
        for clave, info in hipotesis_necesidad.items():
            filas.append((necesidad, clave, info["peso"], info["soporte"], info["total_producto"]))
    filas.sort(key=lambda f: f[2], reverse=True)

    print(f"Modelo anterior respaldado en pesos_hipotesis_anterior.json: {'sí' if hubo_anterior else 'no había uno todavía'}")
    print(f"Guardado en: {RUTA_SALIDA}")
    print()

    registros_sinteticos = resultado["registros_sinteticos"]
    registros_reales = resultado["registros_reales"]
    print(f"Registros sintéticos usados: {registros_sinteticos}")
    print(f"Registros reales usados: {registros_reales}")
    print(f"Total combinado: {registros_sinteticos + registros_reales}")
    if registros_reales == 0:
        print("Aún no hay datos reales — entrenamiento solo con datos sintéticos")
    else:
        print(f"Entrenamiento enriquecido con {registros_reales} registros reales")
    print()

    print("Top 5 pesos más altos:")
    for necesidad, clave, peso, soporte, total_producto in filas[:5]:
        print(f"  {necesidad}.{clave}: peso={peso} (soporte={soporte}/{total_producto})")

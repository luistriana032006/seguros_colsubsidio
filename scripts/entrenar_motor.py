"""Calcula el peso real de cada hipótesis a partir de data/sintetico/datos_sinteticos.csv
y lo guarda en data/modelos/pesos_hipotesis.json.

peso = (filas que cumplen la condición Y compraron ese producto) / (total de filas que
compraron ese producto). Cuando una hipótesis tiene varios productos candidatos (p. ej.
SALUD-01/ASMED-01 para drogueria_activa), "ese producto" se toma como la unión de todos
-- el denominador cuenta filas cuyo producto_comprado esté en esa lista, no un solo ID.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RUTA_DATOS = RAIZ / "data" / "sintetico" / "datos_sinteticos.csv"
RUTA_SALIDA = RAIZ / "data" / "modelos" / "pesos_hipotesis.json"

FLOOR_MINIMO = 0.05
PESO_SIN_DATOS = 0.01

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


def _calcular_peso(df, condicion, productos, ajuste=None):
    mascara_producto = df["producto_comprado"].isin(productos)
    total_producto = int(mascara_producto.sum())

    mascara_condicion = df.eval(condicion, engine="python")
    soporte = int((mascara_condicion & mascara_producto).sum())

    if total_producto == 0:
        peso = PESO_SIN_DATOS
    else:
        peso = soporte / total_producto
        if peso < FLOOR_MINIMO:
            peso = FLOOR_MINIMO

    if ajuste is not None:
        peso += ajuste

    return round(peso, 4), soporte, total_producto


def entrenar():
    df = pd.read_csv(RUTA_DATOS)

    pesos = {}
    for necesidad, hipotesis_necesidad in HIPOTESIS_A_CALCULAR.items():
        pesos[necesidad] = {}
        for clave, definicion in hipotesis_necesidad.items():
            peso, soporte, total_producto = _calcular_peso(
                df, definicion["condicion"], definicion["productos"], definicion.get("ajuste")
            )
            pesos[necesidad][clave] = {
                "peso": peso,
                "productos": definicion["productos"],
                "soporte": soporte,
                "total_producto": total_producto,
            }

    salida = {
        "version": "v1",
        "fecha_entrenamiento": datetime.now(timezone.utc).isoformat(),
        "total_registros_entrenamiento": len(df),
        "pesos": pesos,
    }

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(RUTA_SALIDA, "w", encoding="utf-8") as archivo:
        json.dump(salida, archivo, ensure_ascii=False, indent=2)

    return salida


if __name__ == "__main__":
    resultado = entrenar()

    filas = []
    for necesidad, hipotesis_necesidad in resultado["pesos"].items():
        for clave, info in hipotesis_necesidad.items():
            filas.append((necesidad, clave, info["peso"], info["soporte"], info["total_producto"]))
    filas.sort(key=lambda f: f[2], reverse=True)

    print(f"Registros de entrenamiento: {resultado['total_registros_entrenamiento']}")
    print(f"Guardado en: {RUTA_SALIDA}")
    print()
    print("Top 5 pesos más altos:")
    for necesidad, clave, peso, soporte, total_producto in filas[:5]:
        print(f"  {necesidad}.{clave}: peso={peso} (soporte={soporte}/{total_producto})")

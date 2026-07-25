"""
Genera el dataset sintetico de prueba para el motor generico de reglas.

500 clientes, columnas puramente socioeconomicas (sin nada de Colsubsidio ni
seguros): cliente_id, edad, estado_civil, numero_hijos, nivel_estudios,
rango_ingresos, estabilidad_laboral, region_geografica.

No es random puro: hay correlaciones deliberadas para que las hipotesis de
prueba tengan señal real y no ruido, como pidio el usuario:
  - Pensionado -> mas probable edad 55+
  - Posgrado -> mas probable ingreso Nivel 4-5
  - Mas hijos -> mas probable Casado/Union Libre

DECISIÓN PROPIA: el orden de generación importa. Se genera primero
estabilidad_laboral y nivel_estudios y edad de forma correlacionada entre si
(edad primero, siendo el "ancla" de la que dependen las demas), y luego
numero_hijos y estado_civil correlacionados entre si. No se pidió un orden
exacto ni la fuerza de la correlación, así que se eligió una intensidad
moderada (no determinista: p. ej. "Pensionado" con edad 55+ es MÁS probable,
no obligatorio) para que el dataset siga pareciendo real y no una tabla de
verdad hardcodeada.

Uso:  python3 scripts/generar_dataset_sintetico.py
"""

import json
import random
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ARCHIVO_SALIDA = BASE / "data" / "datasets" / "clientes_socioeconomico.json"

N = 500
SEED = 42  # reproducible: correr el script dos veces da el mismo dataset

CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga",
            "Cartagena", "Pereira", "Manizales"]
# Pesos realistas: mas poblacion en las 4 ciudades grandes.
PESOS_CIUDAD = [30, 18, 14, 10, 8, 8, 6, 6]

ESTADOS_CIVILES = ["Soltero", "Casado", "Divorciado", "Viudo", "Unión Libre"]
NIVELES_ESTUDIO = ["Primaria", "Secundaria", "Técnico", "Universitario", "Posgrado"]
RANGOS_INGRESO = ["Nivel 1", "Nivel 2", "Nivel 3", "Nivel 4", "Nivel 5"]
ESTABILIDADES = ["Empleado", "Freelance", "Dueño", "Pensionado"]


def _edad() -> int:
    # Distribucion realista: mas densidad entre 25 y 55, colas hacia 18 y 80.
    return max(18, min(80, round(random.triangular(18, 80, 38))))


def _estabilidad_laboral(edad: int) -> str:
    # Pensionado se vuelve mas probable con la edad, sin ser determinista.
    if edad >= 62:
        pesos = [15, 5, 15, 65]
    elif edad >= 55:
        pesos = [35, 15, 20, 30]
    else:
        pesos = [60, 20, 18, 2]
    return random.choices(ESTABILIDADES, weights=pesos, k=1)[0]


def _nivel_estudios() -> str:
    return random.choices(NIVELES_ESTUDIO, weights=[10, 30, 25, 25, 10], k=1)[0]


def _rango_ingresos(nivel_estudios: str, estabilidad: str) -> str:
    # Posgrado sube el piso de ingresos; Dueño tambien tiende a ingresos altos.
    pesos = [20, 25, 25, 20, 10]
    if nivel_estudios == "Posgrado":
        pesos = [3, 7, 20, 35, 35]
    elif nivel_estudios == "Universitario":
        pesos = [8, 15, 27, 30, 20]
    if estabilidad == "Dueño":
        pesos = [max(1, p - 5) for p in pesos[:3]] + [p + 8 for p in pesos[3:]]
    return random.choices(RANGOS_INGRESO, weights=pesos, k=1)[0]


def _estado_civil(edad: int) -> str:
    if edad < 25:
        pesos = [70, 15, 2, 0, 13]
    elif edad < 45:
        pesos = [25, 45, 10, 1, 19]
    elif edad < 65:
        pesos = [12, 55, 15, 5, 13]
    else:
        pesos = [8, 45, 10, 30, 7]
    return random.choices(ESTADOS_CIVILES, weights=pesos, k=1)[0]


def _numero_hijos(estado_civil: str, edad: int) -> int:
    # Casado/Union Libre -> mas probable tener hijos. Tambien crece con la edad.
    base = 0
    if estado_civil in ("Casado", "Unión Libre"):
        base = 1
    tope = 5
    lam = 0.6 + base * 1.1 + max(0, (edad - 25)) * 0.02
    hijos = min(tope, round(random.gammavariate(1.6, lam / 1.6)))
    return max(0, hijos)


def generar() -> list[dict]:
    random.seed(SEED)
    filas = []
    for cliente_id in range(1, N + 1):
        edad = _edad()
        estabilidad = _estabilidad_laboral(edad)
        estudios = _nivel_estudios()
        ingresos = _rango_ingresos(estudios, estabilidad)
        civil = _estado_civil(edad)
        hijos = _numero_hijos(civil, edad)
        ciudad = random.choices(CIUDADES, weights=PESOS_CIUDAD, k=1)[0]
        filas.append({
            "cliente_id": cliente_id,
            "edad": edad,
            "estado_civil": civil,
            "numero_hijos": hijos,
            "nivel_estudios": estudios,
            "rango_ingresos": ingresos,
            "estabilidad_laboral": estabilidad,
            "region_geografica": ciudad,
        })
    return filas


def main() -> None:
    ARCHIVO_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    filas = generar()
    ARCHIVO_SALIDA.write_text(json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generadas {len(filas)} filas -> {ARCHIVO_SALIDA}")

    # Verificacion rapida de que las correlaciones pedidas SI aparecen.
    pens = [f for f in filas if f["estabilidad_laboral"] == "Pensionado"]
    pens_mayor = sum(1 for f in pens if f["edad"] >= 55)
    print(f"  Pensionados con edad>=55: {pens_mayor}/{len(pens)} "
          f"({pens_mayor/len(pens):.0%})" if pens else "  Pensionados: 0")

    pos = [f for f in filas if f["nivel_estudios"] == "Posgrado"]
    pos_alto = sum(1 for f in pos if f["rango_ingresos"] in ("Nivel 4", "Nivel 5"))
    print(f"  Posgrado con ingreso Nivel 4-5: {pos_alto}/{len(pos)} "
          f"({pos_alto/len(pos):.0%})" if pos else "  Posgrado: 0")

    con_hijos = [f for f in filas if f["numero_hijos"] > 0]
    con_hijos_pareja = sum(1 for f in con_hijos if f["estado_civil"] in ("Casado", "Unión Libre"))
    print(f"  Con hijos y Casado/Unión Libre: {con_hijos_pareja}/{len(con_hijos)} "
          f"({con_hijos_pareja/len(con_hijos):.0%})" if con_hijos else "  Con hijos: 0")


if __name__ == "__main__":
    main()

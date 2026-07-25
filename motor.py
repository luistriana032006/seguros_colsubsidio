"""
Motor GENERICO de reglas de propension.

No sabe nada de ningun dominio especifico (seguros, negocio concreto, ni ninguna
columna en particular). Recibe tres cosas — un perfil, la ruta a un dataset,
y la ruta a un archivo de hipotesis — y devuelve una recomendacion. Si se
cambia el dataset o las hipotesis, el motor funciona igual sin tocar una
sola linea de este archivo: toda la logica que "sabe" de un dominio vive en
los archivos JSON/CSV de `data/`, no aqui.

FORMATO DE UNA HIPOTESIS (archivo JSON en data/hipotesis/)
------------------------------------------------------------
El archivo es una lista de reglas, o un objeto {"hipotesis": [...]} si se
quiere agregar metadata alrededor (nota, dataset recomendado, etc.) — ambas
formas se aceptan. DECISION PROPIA: esto no estaba especificado; se eligio
para poder documentar limitaciones dentro del propio archivo de hipotesis
sin romper el parser (ver el archivo de ejemplo con hipotesis del dominio anterior en data/hipotesis/).

Cada regla es uno de estos dos formatos:

  Atomica (una sola columna):
    {"columna": "...", "operador": "==|>|<|>=|<=|in", "valor": ..., "categoria_destino": "..."}

  Compuesta (AND de varias columnas — DECISION PROPIA, ver mas abajo):
    {"condiciones": [{"columna": "...", "operador": "...", "valor": "..."}, ...],
     "categoria_destino": "..."}

DECISION PROPIA — regla compuesta: el formato pedido en el prompt es
estrictamente de una columna por regla. Pero una de las hipotesis de prueba
pedidas explicitamente ("numero_hijos == 0 AND estado_civil == Soltero") es
un AND de dos columnas, que no cabe en ese formato. Se extendio el esquema
con la forma "condiciones" (lista de sub-condiciones, todas deben cumplirse)
en vez de inventar una sintaxis de texto libre a parsear. El formato atomico
original sigue funcionando exactamente igual.

PESO AUTOMATICO
----------------
peso = (filas del dataset que cumplen la condicion) / (total de filas)
Si peso < 0.05, se sube a 0.01 — no es 0 (la regla "existe" y puede
activarse), pero pesa casi nada. Esto es literal a lo pedido: no hay pesos
de negocio hardcodeados en ningun lado, todo sale de medir el dataset.

REGLA DE NULOS / NO-CUMPLE
----------------------------
DECISION PROPIA (interpretacion del prompt, documentada porque el texto
podia leerse de dos formas): se distinguen dos casos que el motor anterior
(especifico del dominio anterior) ya distinguia y que aqui se preserva:
  - La columna de la regla NO esta en el perfil, o esta en null/None:
    la regla no se puede evaluar -> va a `reglas_omitidas`. No suma ni resta.
  - La columna SI tiene dato, pero el dato no cumple la condicion:
    la regla simplemente no se activa (no suma). No se lista en ningun lado
    especial — es una evaluacion normal que dio negativo, no una omision.
Mezclar ambos casos en una sola lista habria sido tecnicamente valido segun
la letra del prompt, pero perdia informacion util para explicar la
recomendacion (que es justo el punto de reglas_omitidas).

NORMALIZACION DE SCORES
-------------------------
DECISION PROPIA: el prompt pide "normalizar entre 0 y 1" sin dar la formula
exacta. El score de una categoria es la SUMA de los pesos de sus reglas
activadas, que puede superar 1.0 si varias reglas de la misma categoria se
disparan a la vez. Se eligio la normalizacion mas directa que garantiza el
rango pedido sin inventar una redistribucion mas compleja: score_categoria
= min(1.0, suma_de_pesos_activados). Es el mismo criterio que ya se usaba
para una categoria del motor de dominio especifico anterior a este refactor.

Uso:
    from motor import recomendar
    recomendar(
        perfil={"edad": 35, "numero_hijos": 2, ...},
        ruta_dataset="data/datasets/clientes_socioeconomico.json",
        ruta_hipotesis="data/hipotesis/hipotesis_socioeconomico.json",
    )
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
RUTA_DB = BASE / "seguros.db"
DIR_DATASETS = BASE / "data" / "datasets"
DIR_HIPOTESIS = BASE / "data" / "hipotesis"

UMBRAL_PESO_MINIMO = 0.05
PESO_MINIMO_FORZADO = 0.01
UMBRAL_ESCALAMIENTO = 0.2
UMBRAL_CONFIANZA_ALTA = 0.6
UMBRAL_CONFIANZA_MEDIA = 0.3

OPERADORES_VALIDOS = ("==", ">", "<", ">=", "<=", "in")


# ---------------------------------------------------------------------------
# CARGA DE DATASET Y DE HIPOTESIS
# ---------------------------------------------------------------------------
def cargar_dataset(ruta: str | Path) -> pd.DataFrame:
    """Carga un dataset desde CSV o JSON, detectando el formato por extension."""
    ruta = Path(ruta)
    if ruta.suffix.lower() == ".csv":
        df = pd.read_csv(ruta)
    elif ruta.suffix.lower() == ".json":
        with ruta.open(encoding="utf-8") as f:
            registros = json.load(f)
        df = pd.DataFrame(registros)
    else:
        raise ValueError(f"Formato de dataset no soportado: {ruta.suffix} (solo .csv o .json)")
    return df.where(pd.notnull(df), None)


def cargar_hipotesis(ruta: str | Path) -> list[dict]:
    """Carga la lista de reglas desde un archivo JSON. Acepta lista plana o
    {"hipotesis": [...]}. Cualquier otra clave del dict se ignora (metadata)."""
    with Path(ruta).open(encoding="utf-8") as f:
        data = json.load(f)
    reglas = data["hipotesis"] if isinstance(data, dict) else data
    for i, regla in enumerate(reglas):
        if "categoria_destino" not in regla:
            raise ValueError(f"Regla #{i} sin 'categoria_destino': {regla}")
        if "condiciones" not in regla and "columna" not in regla:
            raise ValueError(f"Regla #{i} no tiene 'columna' ni 'condiciones': {regla}")
    return reglas


def _condiciones_de(regla: dict) -> list[dict]:
    """Normaliza una regla (atomica o compuesta) a su lista de sub-condiciones."""
    if "condiciones" in regla:
        return regla["condiciones"]
    return [{"columna": regla["columna"], "operador": regla["operador"], "valor": regla["valor"]}]


def listar_datasets() -> list[Path]:
    return sorted(DIR_DATASETS.glob("*")) if DIR_DATASETS.exists() else []


def listar_hipotesis() -> list[Path]:
    return sorted(DIR_HIPOTESIS.glob("*.json")) if DIR_HIPOTESIS.exists() else []


def columnas_usadas(ruta_hipotesis: str | Path) -> list[str]:
    """Columnas distintas que mencionan las reglas de un archivo de hipotesis,
    en orden de aparicion. Sirve para que un formulario muestre solo los
    campos relevantes."""
    vistas, orden = set(), []
    for regla in cargar_hipotesis(ruta_hipotesis):
        for c in _condiciones_de(regla):
            if c["columna"] not in vistas:
                vistas.add(c["columna"])
                orden.append(c["columna"])
    return orden


# ---------------------------------------------------------------------------
# EVALUACION DE CONDICIONES — vectorizada (peso) y escalar (perfil)
# ---------------------------------------------------------------------------
def _mascara_condicion(serie: pd.Series, operador: str, valor) -> pd.Series:
    if operador == "==":
        return serie == valor
    if operador == ">":
        return serie > valor
    if operador == "<":
        return serie < valor
    if operador == ">=":
        return serie >= valor
    if operador == "<=":
        return serie <= valor
    if operador == "in":
        return serie.isin(valor)
    raise ValueError(f"Operador no soportado: {operador!r} (validos: {OPERADORES_VALIDOS})")


def _peso_regla(df: pd.DataFrame, regla: dict) -> float:
    """peso = filas que cumplen TODAS las sub-condiciones / total de filas."""
    mascara = pd.Series(True, index=df.index)
    for c in _condiciones_de(regla):
        col = c["columna"]
        if col not in df.columns:
            return PESO_MINIMO_FORZADO  # la columna no existe en este dataset
        mascara &= _mascara_condicion(df[col], c["operador"], c["valor"]).fillna(False)
    peso = float(mascara.sum()) / len(df) if len(df) else 0.0
    return PESO_MINIMO_FORZADO if peso < UMBRAL_PESO_MINIMO else peso


def _evaluar_condicion_escalar(valor_perfil, operador: str, valor_regla) -> bool:
    if operador == "==":
        return valor_perfil == valor_regla
    if operador == ">":
        return valor_perfil > valor_regla
    if operador == "<":
        return valor_perfil < valor_regla
    if operador == ">=":
        return valor_perfil >= valor_regla
    if operador == "<=":
        return valor_perfil <= valor_regla
    if operador == "in":
        return valor_perfil in valor_regla
    raise ValueError(f"Operador no soportado: {operador!r} (validos: {OPERADORES_VALIDOS})")


def _texto_condicion(c: dict) -> str:
    return f"{c['columna']} {c['operador']} {c['valor']!r}"


def _evaluar_regla_en_perfil(perfil: dict, regla: dict) -> tuple[bool | None, str]:
    """Devuelve (resultado, texto_legible).
    resultado=None significa "no evaluable" (dato faltante) -> va a omitidas.
    resultado=False significa "evaluada, no se activo" -> se ignora en silencio.
    resultado=True significa "se activo"."""
    condiciones = _condiciones_de(regla)
    texto = " Y ".join(_texto_condicion(c) for c in condiciones)
    for c in condiciones:
        valor_perfil = (perfil or {}).get(c["columna"])
        if valor_perfil is None:
            return None, texto
        try:
            if not _evaluar_condicion_escalar(valor_perfil, c["operador"], c["valor"]):
                return False, texto
        except TypeError:
            # tipos incompatibles (ej. comparar texto con numero) -> no se
            # puede evaluar, se trata igual que dato faltante, no se rompe.
            return None, texto
    return True, texto


# ---------------------------------------------------------------------------
# PERSISTENCIA — seguros.db (SQLite, 3 tablas)
#
# ESTO NO ES RAG. seguros.db es un log de auditoria transaccional: guarda que
# perfil entro y que recomendacion salio, para poder reconstruir despues "por
# que se recomendo X". No hay embeddings, no hay vector store, no hay
# busqueda semantica ni retrieval de ningun tipo. La recomendacion misma se
# calcula ANTES de tocar la base de datos, evaluando reglas directas contra
# el dataset (ver recomendar() mas abajo) — la DB solo registra el resultado,
# no participa en calcularlo. Si en el futuro se necesita RAG de verdad (ej.
# buscar fichas de producto en texto libre), es una pieza aparte.
# ---------------------------------------------------------------------------
def _conectar_db() -> sqlite3.Connection:
    con = sqlite3.connect(RUTA_DB)
    con.execute("""CREATE TABLE IF NOT EXISTS perfiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        datos_json TEXT NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS recomendaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        perfil_id INTEGER,
        perfil_entrada TEXT NOT NULL,
        dataset_usado TEXT NOT NULL,
        hipotesis_usadas TEXT NOT NULL,
        categoria_top TEXT,
        categoria_secundaria TEXT,
        score_propension REAL,
        confianza TEXT,
        reglas_activadas TEXT NOT NULL,
        reglas_omitidas TEXT NOT NULL,
        requiere_escalamiento INTEGER NOT NULL,
        FOREIGN KEY (perfil_id) REFERENCES perfiles(id)
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS hipotesis_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        archivo TEXT NOT NULL,
        num_reglas INTEGER NOT NULL,
        timestamp TEXT NOT NULL
    )""")
    con.commit()
    return con


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _registrar_hipotesis(archivo: str, num_reglas: int) -> None:
    con = _conectar_db()
    con.execute("INSERT INTO hipotesis_log (archivo, num_reglas, timestamp) VALUES (?, ?, ?)",
                (archivo, num_reglas, _ahora()))
    con.commit()
    con.close()


def _registrar_recomendacion(perfil: dict, resultado: dict) -> None:
    """Guarda el perfil (tabla perfiles) y la recomendacion completa (tabla
    recomendaciones), incluyendo el perfil_entrada denormalizado dentro de
    recomendaciones — DECISION PROPIA: el prompt pidio la tabla `perfiles`
    con datos_json en una seccion, y por separado pidio que `recomendaciones`
    tambien incluya perfil_entrada completo en otra seccion mas detallada.
    Ambas cosas se implementaron tal cual, aunque quede redundante: el
    objetivo explicito era poder reconstruir "por que se recomendo X" sin
    tener que hacer JOIN, y accesos rapidos por separado a solo perfiles."""
    con = _conectar_db()
    ts = _ahora()
    perfil_json = json.dumps(perfil, ensure_ascii=False)
    cur = con.execute("INSERT INTO perfiles (timestamp, datos_json) VALUES (?, ?)",
                       (ts, perfil_json))
    perfil_id = cur.lastrowid
    con.execute("""INSERT INTO recomendaciones
        (timestamp, perfil_id, perfil_entrada, dataset_usado, hipotesis_usadas,
         categoria_top, categoria_secundaria, score_propension, confianza,
         reglas_activadas, reglas_omitidas, requiere_escalamiento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (ts, perfil_id, perfil_json, resultado["dataset_usado"], resultado["hipotesis_usadas"],
         resultado["categoria_top"], resultado["categoria_secundaria"],
         resultado["score_propension"], resultado["confianza"],
         json.dumps(resultado["reglas_activadas"], ensure_ascii=False),
         json.dumps(resultado["reglas_omitidas"], ensure_ascii=False),
         int(resultado["requiere_escalamiento"])))
    con.commit()
    con.close()


# ---------------------------------------------------------------------------
# FUNCION CENTRAL
# ---------------------------------------------------------------------------
def recomendar(perfil: dict, ruta_dataset: str, ruta_hipotesis: str) -> dict:
    """Recibe un perfil y evalua las hipotesis de `ruta_hipotesis` contra el
    perfil, pesando cada regla segun su frecuencia real en `ruta_dataset`.
    No asume nada sobre las columnas de ninguno de los dos archivos."""
    df = cargar_dataset(ruta_dataset)
    hipotesis = cargar_hipotesis(ruta_hipotesis)
    _registrar_hipotesis(Path(ruta_hipotesis).name, len(hipotesis))

    scores: dict[str, float] = {}
    orden_categorias: list[str] = []
    reglas_activadas: list[str] = []
    reglas_omitidas: list[str] = []

    for regla in hipotesis:
        categoria = regla["categoria_destino"]
        if categoria not in scores:
            scores[categoria] = 0.0
            orden_categorias.append(categoria)

        resultado, texto = _evaluar_regla_en_perfil(perfil, regla)
        if resultado is None:
            reglas_omitidas.append(f"{texto} → {categoria} (dato faltante, se omite)")
            continue
        if resultado is False:
            continue  # evaluada, no aplica: no es omision, simplemente no suma

        peso = _peso_regla(df, regla)
        scores[categoria] += peso
        reglas_activadas.append(f"{texto} → {categoria} (peso {peso:.2f})")

    scores = {c: round(min(1.0, v), 4) for c, v in scores.items()}

    if orden_categorias:
        top = max(orden_categorias, key=lambda c: (scores[c], -orden_categorias.index(c)))
        resto = [c for c in orden_categorias if c != top]
        secundaria = (max(resto, key=lambda c: (scores[c], -orden_categorias.index(c)))
                      if resto else None)
        score_top = scores[top]
    else:
        top, secundaria, score_top = None, None, 0.0

    if score_top > UMBRAL_CONFIANZA_ALTA:
        confianza = "alta"
    elif score_top >= UMBRAL_CONFIANZA_MEDIA:
        confianza = "media"
    else:
        confianza = "baja"

    resultado_final = {
        "categoria_top": top,
        "categoria_secundaria": secundaria,
        "score_propension": score_top,
        "confianza": confianza,
        "reglas_activadas": reglas_activadas,
        "reglas_omitidas": reglas_omitidas,
        "requiere_escalamiento": score_top < UMBRAL_ESCALAMIENTO,
        "dataset_usado": Path(ruta_dataset).name,
        "hipotesis_usadas": Path(ruta_hipotesis).name,
        "scores_por_categoria": scores,
    }

    _registrar_recomendacion(perfil, resultado_final)
    return resultado_final


if __name__ == "__main__":
    perfil_demo = {
        "edad": 35, "estado_civil": "Casado", "numero_hijos": 2,
        "nivel_estudios": "Universitario", "rango_ingresos": "Nivel 2",
        "estabilidad_laboral": "Empleado", "region_geografica": "Bogotá",
    }
    salida = recomendar(
        perfil_demo,
        DIR_DATASETS / "clientes_socioeconomico.json",
        DIR_HIPOTESIS / "hipotesis_socioeconomico.json",
    )
    print(json.dumps(salida, ensure_ascii=False, indent=2))

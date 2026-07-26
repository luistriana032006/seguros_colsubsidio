"""Crea data/motor.db (SQLite): tablas catalogo, usuarios y recomendaciones.

Si motor.db ya existe, no se sobreescribe: las tablas se crean solo si faltan
(CREATE TABLE IF NOT EXISTS) y el catálogo solo se migra si la tabla catalogo
está vacía -- así una corrida repetida nunca borra usuarios/recomendaciones ya
guardados por motor.registrar().
"""
import sqlite3
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CATALOGO_CSV = RAIZ / "data" / "catalogo" / "catalogo_productos.csv"
RUTA_DB = RAIZ / "data" / "motor.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS catalogo (
    producto_id TEXT PRIMARY KEY,
    nombre TEXT,
    categoria TEXT,
    precio_desde TEXT,
    estado_precio TEXT,
    campos_verificados INTEGER
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_interno TEXT,
    id_contacto TEXT,
    necesidad TEXT,
    edad INTEGER,
    ciudad TEXT,
    rango_salarial TEXT,
    tipo_vivienda TEXT,
    tiene_dependientes INTEGER,
    num_dependientes INTEGER,
    estado_civil TEXT,
    usa_drogueria INTEGER,
    usa_hoteles INTEGER,
    usa_agencias INTEGER,
    tiene_mascota INTEGER,
    tipo_mascota TEXT,
    tipo_vehiculo TEXT,
    canal TEXT,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS recomendaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    producto_principal TEXT,
    producto_alternativa TEXT,
    categoria TEXT,
    score REAL,
    confianza TEXT,
    hipotesis_activadas TEXT,
    razon TEXT,
    timestamp TEXT,
    recomendaciones_json TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
"""


def _migrar_columna_recomendaciones_json(conexion):
    """DBs creadas antes de que recomendar() devolviera 3 recomendaciones no tienen
    esta columna todavía -- CREATE TABLE IF NOT EXISTS no la agrega sola."""
    columnas = {fila[1] for fila in conexion.execute("PRAGMA table_info(recomendaciones)").fetchall()}
    if "recomendaciones_json" not in columnas:
        conexion.execute("ALTER TABLE recomendaciones ADD COLUMN recomendaciones_json TEXT")
        conexion.commit()


def _cargar_catalogo():
    """Migra catalogo_productos.csv a las columnas pedidas para la tabla catalogo."""
    catalogo = pd.read_csv(RUTA_CATALOGO_CSV)
    columnas_estado = [c for c in catalogo.columns if c.startswith("estado_")]
    catalogo["campos_verificados"] = catalogo[columnas_estado].eq("verificado").sum(axis=1)
    return catalogo[
        ["producto_id", "nombre_producto", "categoria", "precio", "estado_precio", "campos_verificados"]
    ].rename(columns={"nombre_producto": "nombre", "precio": "precio_desde"})


def crear_db():
    RUTA_DB.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(RUTA_DB)
    try:
        conexion.executescript(ESQUEMA)
        conexion.commit()
        _migrar_columna_recomendaciones_json(conexion)

        total = conexion.execute("SELECT COUNT(*) FROM catalogo").fetchone()[0]
        if total == 0:
            catalogo = _cargar_catalogo()
            catalogo.to_sql("catalogo", conexion, if_exists="append", index=False)
            conexion.commit()
            total = conexion.execute("SELECT COUNT(*) FROM catalogo").fetchone()[0]
        else:
            print(f"La tabla catalogo ya tenía {total} productos -- no se sobreescribe.")

        return total
    finally:
        conexion.close()


if __name__ == "__main__":
    ya_existia = RUTA_DB.exists()
    total_productos = crear_db()
    print(f"Base de datos: {RUTA_DB} ({'ya existía' if ya_existia else 'creada'})")
    print(f"Productos en la tabla catalogo: {total_productos}")

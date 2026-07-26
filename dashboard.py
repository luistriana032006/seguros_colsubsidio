"""Dashboard Streamlit de solo lectura sobre data/motor.db.

No genera datos -- motor.registrar() es quien escribe en la DB cada vez que
recomendar() resuelve un perfil. Este dashboard solo lee y muestra métricas.
Estructura de tablas: ver scripts/crear_db.py. Campos de recomendar(): ver motor.py.
"""
import json
import sqlite3
from collections import Counter
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

RAIZ = Path(__file__).resolve().parent
RUTA_DB = RAIZ / "data" / "motor.db"

st.set_page_config(page_title="Dashboard — motor de recomendación", page_icon="📊", layout="wide")

try:
    from streamlit_autorefresh import st_autorefresh

    st_autorefresh(interval=10000, limit=None, key="dashboard_refresh")
except ImportError:
    import streamlit.components.v1 as components

    components.html(
        "<script>setTimeout(function(){window.location.reload();}, 10000);</script>",
        height=0,
    )


@st.cache_data(ttl=10)
def cargar_datos():
    """Lee catalogo/usuarios/recomendaciones de motor.db. None si la DB o las tablas no existen."""
    if not RUTA_DB.exists():
        return None

    conexion = sqlite3.connect(RUTA_DB)
    try:
        tablas = {
            fila[0] for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        requeridas = {"catalogo", "usuarios", "recomendaciones"}
        if not requeridas.issubset(tablas):
            return None

        catalogo = pd.read_sql_query("SELECT * FROM catalogo", conexion)
        usuarios = pd.read_sql_query("SELECT * FROM usuarios", conexion)
        recomendaciones = pd.read_sql_query("SELECT * FROM recomendaciones", conexion)
    finally:
        conexion.close()

    return {"catalogo": catalogo, "usuarios": usuarios, "recomendaciones": recomendaciones}


st.title("Dashboard del motor de recomendación")
st.caption("Lectura en vivo de data/motor.db — no genera datos, solo los muestra.")

if st.button("Refrescar ahora"):
    cargar_datos.clear()

datos = cargar_datos()

if datos is None or datos["recomendaciones"].empty:
    st.info("El motor aún no ha procesado ninguna recomendación.")
    st.stop()

catalogo_df = datos["catalogo"]
usuarios_df = datos["usuarios"]
recomendaciones_df = datos["recomendaciones"]

# --- Sección 1: métricas globales ---
st.header("1. Métricas globales")

total_recomendaciones = len(recomendaciones_df)
pct_confianza_alta = (recomendaciones_df["confianza"] == "alta").mean() * 100
producto_top_id = recomendaciones_df["producto_principal"].value_counts().idxmax()
nombres_por_id = catalogo_df.set_index("producto_id")["nombre"].to_dict()
producto_top_label = nombres_por_id.get(producto_top_id, producto_top_id)
necesidad_top = usuarios_df["necesidad"].value_counts().idxmax()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total recomendaciones", total_recomendaciones)
col2.metric("Confianza alta", f"{pct_confianza_alta:.0f}%")
col3.metric("Producto más recomendado", producto_top_label)
col4.metric("Necesidad más frecuente", necesidad_top)

# --- Sección 2: distribución de productos ---
st.header("2. Distribución de productos")

conteo_productos = recomendaciones_df["producto_principal"].value_counts().sort_values(ascending=True)
etiquetas = [f"{nombres_por_id.get(pid, pid)} ({pid})" for pid in conteo_productos.index]
fig_productos = px.bar(
    x=conteo_productos.values, y=etiquetas, orientation="h",
    labels={"x": "Veces recomendado", "y": "Producto"},
)
st.plotly_chart(fig_productos, use_container_width=True)

# --- Sección 3: distribución de confianza ---
st.header("3. Distribución de confianza")

conteo_confianza = recomendaciones_df["confianza"].value_counts().reindex(
    ["alta", "media", "baja"]
).dropna()
fig_confianza = px.pie(
    values=conteo_confianza.values, names=conteo_confianza.index,
    color=conteo_confianza.index,
    color_discrete_map={"alta": "green", "media": "gold", "baja": "red"},
)
st.plotly_chart(fig_confianza, use_container_width=True)

# --- Sección 4: actividad en el tiempo ---
st.header("4. Actividad en el tiempo")

timestamps = pd.to_datetime(recomendaciones_df["timestamp"], utc=True, errors="coerce").dropna()
if len(timestamps) < 5:
    st.info("Aún no hay suficientes datos.")
else:
    por_hora = timestamps.dt.hour.value_counts().sort_index()
    por_hora = por_hora.reindex(range(24), fill_value=0)
    fig_actividad = px.line(
        x=por_hora.index, y=por_hora.values,
        labels={"x": "Hora del día", "y": "Recomendaciones"},
        markers=True,
    )
    st.plotly_chart(fig_actividad, use_container_width=True)

# --- Sección 5: hipótesis más activadas ---
st.header("5. Hipótesis más activadas")

contador_hipotesis = Counter()
for texto in recomendaciones_df["hipotesis_activadas"].dropna():
    try:
        hipotesis = json.loads(texto)
    except (TypeError, ValueError):
        continue
    contador_hipotesis.update(hipotesis)

if not contador_hipotesis:
    st.info("Ninguna recomendación registrada activó una hipótesis todavía.")
else:
    tabla_hipotesis = pd.DataFrame(
        contador_hipotesis.most_common(), columns=["Hipótesis", "Veces activada"]
    )
    st.dataframe(tabla_hipotesis, use_container_width=True, hide_index=True)

# --- Sección 6: últimas 10 recomendaciones ---
st.header("6. Últimas 10 recomendaciones")

ultimas = (
    recomendaciones_df.merge(
        usuarios_df[["id", "necesidad", "canal"]], left_on="usuario_id", right_on="id", how="left"
    )
    .sort_values("timestamp", ascending=False)
    .head(10)
)[["timestamp", "necesidad", "producto_principal", "confianza", "score", "canal"]]
st.dataframe(ultimas, use_container_width=True, hide_index=True)

# --- Sección 7: distribución por canal ---
st.header("7. Distribución por canal")

conteo_canal = usuarios_df["canal"].value_counts()
fig_canal = px.bar(x=conteo_canal.index, y=conteo_canal.values, labels={"x": "Canal", "y": "Recomendaciones"})
st.plotly_chart(fig_canal, use_container_width=True)

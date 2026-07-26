"""Dashboard standalone de métricas -- ver metricas.py para la lógica real.

Existe como página independiente (make dashboard, puerto 8502) además de la
pestaña "Métricas" de app.py -- las dos comparten el mismo render_metricas(),
ninguna duplica la lógica.
"""
import streamlit as st

from metricas import render_metricas

st.set_page_config(page_title="Dashboard — motor de recomendación", page_icon="📊", layout="wide")
st.title("Dashboard del motor de recomendación")
st.caption("Lectura en vivo de data/motor.db — no genera datos, solo los muestra.")

render_metricas()

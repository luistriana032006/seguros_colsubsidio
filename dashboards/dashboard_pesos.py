"""Dashboard standalone de pesos de hipótesis -- ver pesos.py para la lógica real.

Existe como página independiente (make pesos, puerto 8503) además de la pestaña
"⚖️ Pesos" de app.py -- las dos comparten el mismo render_pesos(), ninguna
duplica la lógica.
"""
import sys
from pathlib import Path

# streamlit run dashboards/dashboard_pesos.py pone dashboards/ en sys.path, no la
# raíz del repo -- sin esto, "from dashboards.pesos import ..." no resolvería.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from dashboards.pesos import render_pesos

st.set_page_config(page_title="Pesos de hipótesis — motor de recomendación", page_icon="⚖️", layout="wide")
st.title("Pesos de las hipótesis del motor")
st.caption("Lectura en vivo de data/modelos/pesos_hipotesis.json — no genera datos.")

render_pesos()

"""Dashboard standalone de métricas -- ver metricas.py para la lógica real.

Existe como página independiente (make dashboard, puerto 8502) además de la
pestaña "Métricas" de app.py -- las dos comparten el mismo render_metricas(),
ninguna duplica la lógica.
"""
import sys
from pathlib import Path

# streamlit run dashboards/dashboard.py pone dashboards/ en sys.path, no la raíz
# del repo -- sin esto, "from dashboards.metricas import ..." no resolvería.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from dashboards.metricas import render_metricas

st.set_page_config(page_title="Dashboard — motor de recomendación", page_icon="📊", layout="wide")
st.title("Dashboard del motor de recomendación")
st.caption("Lectura en vivo de data/motor.db — no genera datos, solo los muestra.")

render_metricas()

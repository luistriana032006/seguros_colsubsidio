"""Dashboard standalone de pesos de hipótesis -- ver pesos.py para la lógica real.

Existe como página independiente (make pesos, puerto 8503) además de la pestaña
"⚖️ Pesos" de app.py -- las dos comparten el mismo render_pesos(), ninguna
duplica la lógica.
"""
import streamlit as st

from pesos import render_pesos

st.set_page_config(page_title="Pesos de hipótesis — motor de recomendación", page_icon="⚖️", layout="wide")
st.title("Pesos de las hipótesis del motor")
st.caption("Lectura en vivo de data/modelos/pesos_hipotesis.json — no genera datos.")

render_pesos()

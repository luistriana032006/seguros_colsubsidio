"""Demo Streamlit del motor GENERICO de reglas. Una sola pagina.

No sabe nada de ningun dominio: el dropdown de dataset y el de hipotesis
determinan que columnas pide el formulario y que categorias puede devolver.
Cambiar de dominio (seguros, socioeconomico, o cualquier otro) es
elegir otro archivo en los dropdowns, no tocar este archivo ni motor.py.

    streamlit run app.py
"""

import json

import streamlit as st

from motor import (columnas_usadas, listar_datasets, listar_hipotesis,
                   recomendar)

st.set_page_config(page_title="Motor genérico de recomendación", page_icon="🧩", layout="wide")

st.title("🧩 Motor genérico de reglas")
st.caption("Evalúa hipótesis de propensión contra cualquier dataset y perfil. "
           "No sabe nada de ningún dominio específico — el dataset y las hipótesis lo definen todo.")

if "perfil_actual" not in st.session_state:
    st.session_state.perfil_actual = None

# ---------------------------------------------------------------- selección de fuente
st.subheader("1. Elegí el dataset y las hipótesis")
c1, c2 = st.columns(2)
datasets = listar_datasets()
archivos_hipotesis = listar_hipotesis()

if not datasets or not archivos_hipotesis:
    st.error("No hay datasets o hipótesis en `data/datasets/` y `data/hipotesis/`.")
    st.stop()

with c1:
    ruta_dataset = st.selectbox("Dataset", datasets, format_func=lambda p: p.name)
with c2:
    ruta_hipotesis = st.selectbox("Hipótesis", archivos_hipotesis, format_func=lambda p: p.name)

campos = columnas_usadas(ruta_hipotesis)
st.caption(f"Este archivo de hipótesis usa {len(campos)} campo(s): " + ", ".join(f"`{c}`" for c in campos))

st.divider()

# ---------------------------------------------------------------- formulario dinámico
st.subheader("2. Armá un perfil")
st.caption("El formulario solo pide los campos que las hipótesis elegidas realmente usan.")

with st.form("formulario_perfil"):
    valores = {}
    cols_form = st.columns(3)
    for i, campo in enumerate(campos):
        with cols_form[i % 3]:
            valores[campo] = st.text_input(campo, key=f"campo_{campo}")

    enviado = st.form_submit_button("Recomendar", type="primary", use_container_width=True)
    if enviado:
        perfil = {}
        for campo, texto in valores.items():
            texto = texto.strip()
            if not texto:
                continue  # campo vacío = dato ausente, la regla que lo usa se omite
            # DECISION PROPIA: intento numero si se puede, si no lo dejo como
            # texto. El motor compara tal cual llegue el valor; si el tipo no
            # calza con la regla, esa regla se omite en vez de romper (ver
            # _evaluar_regla_en_perfil en motor.py).
            try:
                valor = int(texto)
            except ValueError:
                try:
                    valor = float(texto)
                except ValueError:
                    valor = texto
            perfil[campo] = valor
        st.session_state.perfil_actual = (perfil, str(ruta_dataset), str(ruta_hipotesis))

st.divider()

# ---------------------------------------------------------------- resultado
if st.session_state.perfil_actual is not None:
    perfil, ds, hip = st.session_state.perfil_actual
    r = recomendar(perfil, ds, hip)

    st.subheader("3. Resultado")
    izq, der = st.columns([1, 1])

    with izq:
        if r["categoria_top"] is None:
            st.error("El archivo de hipótesis no define ninguna categoría.")
        else:
            st.metric("Categoría", r["categoria_top"], f"score {r['score_propension']}")
            st.markdown(f"**Confianza:** {r['confianza']}")
            if r["categoria_secundaria"]:
                st.markdown(f"**Segunda opción:** {r['categoria_secundaria']}")
            if r["requiere_escalamiento"]:
                st.warning("`requiere_escalamiento = true` — señal débil, hace falta más información.")

        st.markdown("**Reglas activadas:**")
        if r["reglas_activadas"]:
            for regla in r["reglas_activadas"]:
                st.markdown(f"- `{regla}`")
        else:
            st.caption("Ninguna.")

        if r["reglas_omitidas"]:
            with st.expander(f"Reglas omitidas por falta de dato ({len(r['reglas_omitidas'])})"):
                for o in r["reglas_omitidas"]:
                    st.markdown(f"- {o}")

        if r["scores_por_categoria"]:
            st.markdown("**Score por categoría:**")
            st.bar_chart(r["scores_por_categoria"], horizontal=True, height=220)

    with der:
        st.subheader("Salida JSON")
        st.json(r)
        st.subheader("Perfil de entrada")
        st.code(json.dumps(perfil, ensure_ascii=False, indent=2), language="json")

st.divider()
st.caption("Cada recomendación queda registrada en `seguros.db` "
           "(tablas `perfiles`, `recomendaciones`, `hipotesis_log`).")

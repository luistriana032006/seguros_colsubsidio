"""Interfaz Streamlit para probar motor.recomendar() manualmente, con las métricas del motor."""
import streamlit as st

from dashboards.metricas import render_metricas
from dashboards.pesos import render_pesos
from motor import recomendar, registrar

st.set_page_config(page_title="Motor de recomendación de seguros", page_icon="🛡️", layout="wide")
st.title("Motor de recomendación de seguros")

tab_prueba, tab_metricas, tab_pesos = st.tabs(["🧪 Probar el motor", "📊 Métricas", "⚖️ Pesos"])

with tab_prueba:
    st.caption("Interfaz de prueba manual sobre motor.recomendar()")

    st.header("1. Perfil del usuario")

    necesidad = st.selectbox("Necesidad", ["salud", "familia", "hogar", "movilidad", "mascotas", "credito"])
    edad = st.number_input("Edad", min_value=18, max_value=75, value=30, step=1)
    ciudad = st.selectbox(
        "Ciudad",
        ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga",
         "Soacha", "Mosquera", "Zipaquirá", "Funza", "Manizales"],
    )
    rango_salarial = st.selectbox(
        "Rango salarial",
        ["menor_smlv", "1_1.5", "1.5_2", "2_2.5", "2.5_3", "3_4",
         "4_6", "6_8", "8_10", "10_20", "20_30", "mayor_30"],
    )
    tipo_vivienda = st.selectbox("Tipo de vivienda", ["propia", "arrendada", "familiar"])
    tiene_dependientes = st.checkbox("Tiene dependientes")
    num_dependientes = st.number_input(
        "Número de dependientes", min_value=0, max_value=4, value=0, step=1,
        disabled=not tiene_dependientes,
    )
    estado_civil = st.selectbox("Estado civil", ["soltero", "casado", "union_libre", "divorciado", "viudo"])
    usa_drogueria = st.checkbox("Usa droguería")
    usa_hoteles = st.checkbox("Usa hoteles")
    usa_agencias = st.checkbox("Usa agencias")
    tiene_mascota = st.checkbox("Tiene mascota")
    tipo_mascota = st.selectbox("Tipo de mascota", ["perro", "gato", "otro"]) if tiene_mascota else None
    tipo_vehiculo = st.selectbox("Tipo de vehículo", ["carro", "moto", "bici", "ninguno"])

    if st.button("Recomendar"):
        perfil = {
            "necesidad": necesidad,
            "edad": int(edad),
            "ciudad": ciudad,
            "rango_salarial": rango_salarial,
            "tipo_vivienda": tipo_vivienda,
            "tiene_dependientes": tiene_dependientes,
            "num_dependientes": int(num_dependientes) if tiene_dependientes else 0,
            "estado_civil": estado_civil,
            "usa_drogueria": usa_drogueria,
            "usa_hoteles": usa_hoteles,
            "usa_agencias": usa_agencias,
            "tiene_mascota": tiene_mascota,
            "tipo_mascota": tipo_mascota,
            "tipo_vehiculo": tipo_vehiculo,
        }
        try:
            resultado = recomendar(perfil)
            registrar(perfil, resultado, canal="prueba")
            st.session_state["resultado"] = resultado
            st.session_state["error"] = None
        except Exception as error:
            st.session_state["resultado"] = None
            st.session_state["error"] = str(error)

    st.header("2. Resultado")

    error = st.session_state.get("error")
    resultado = st.session_state.get("resultado")

    if error:
        st.error(f"recomendar() lanzó una excepción: {error}")
    elif resultado is None:
        st.caption("Completa el formulario y presiona “Recomendar” para ver un resultado.")
    elif resultado.get("error") is True:
        st.error(resultado.get("mensaje", "Perfil inválido."))
        if resultado.get("campos_faltantes"):
            st.markdown(f"**Campos faltantes:** {', '.join(resultado['campos_faltantes'])}")
        if resultado.get("campos_invalidos"):
            st.markdown("**Campos inválidos:**")
            for detalle in resultado["campos_invalidos"]:
                st.markdown(f"- {detalle}")
    else:
        st.markdown(f"**Necesidad:** {resultado['necesidad']}")

        for item in resultado["recomendaciones"]:
            st.subheader(f"{item['posicion']}. {item['nombre']} — `{item['producto_id']}`")
            st.markdown(f"**Categoría:** {item['categoria']}")

            confianza = item["confianza"]
            texto_confianza = f"Confianza: {confianza}"
            if confianza == "alta":
                st.success(texto_confianza)
            elif confianza == "media":
                st.warning(texto_confianza)
            else:
                st.error(texto_confianza)

            score = float(item["score"])
            st.markdown(f"**Score:** {score:.2f}")
            st.progress(min(max(score, 0.0), 1.0))

            st.markdown("**Razón:**")
            st.info(item["razon"])

        st.markdown("**Hipótesis activadas:**")
        if resultado["hipotesis_activadas"]:
            for hipotesis in resultado["hipotesis_activadas"]:
                st.markdown(f"- {hipotesis}")
        else:
            st.markdown("_Ninguna hipótesis se activó._")

with tab_metricas:
    render_metricas()

with tab_pesos:
    render_pesos()

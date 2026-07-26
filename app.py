"""Interfaz Streamlit para probar motor.recomendar() manualmente."""
import streamlit as st

from motor import CATALOGO, recomendar

st.set_page_config(page_title="Motor de recomendación de seguros", page_icon="🛡️")
st.title("Motor de recomendación de seguros")
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
        st.session_state["resultado"] = recomendar(perfil)
        st.session_state["error"] = None
    except Exception as error:
        st.session_state["resultado"] = None
        st.session_state["error"] = str(error)

st.header("2. Resultado")


def nombre_legible(producto_id):
    if producto_id is None or producto_id not in CATALOGO.index:
        return producto_id
    return str(CATALOGO.loc[producto_id, "nombre_producto"])


error = st.session_state.get("error")
resultado = st.session_state.get("resultado")

if error:
    st.error(f"recomendar() lanzó una excepción: {error}")
elif resultado is None:
    st.caption("Completa el formulario y presiona “Recomendar” para ver un resultado.")
else:
    principal_id = resultado["producto_principal"]
    st.markdown(f"**Producto principal:** {nombre_legible(principal_id)} — `{principal_id}`")

    alternativa_id = resultado["producto_alternativa"]
    if alternativa_id:
        st.markdown(f"**Producto alternativa:** {nombre_legible(alternativa_id)} — `{alternativa_id}`")
    else:
        st.markdown("**Producto alternativa:** ninguna")

    st.markdown(f"**Categoría:** {resultado['categoria']}")

    confianza = resultado["confianza"]
    texto_confianza = f"Confianza: {confianza}"
    if confianza == "alta":
        st.success(texto_confianza)
    elif confianza == "media":
        st.warning(texto_confianza)
    else:
        st.error(texto_confianza)

    score = float(resultado["score"])
    st.markdown(f"**Score:** {score:.2f}")
    st.progress(min(max(score, 0.0), 1.0))

    st.markdown("**Hipótesis activadas:**")
    if resultado["hipotesis_activadas"]:
        for hipotesis in resultado["hipotesis_activadas"]:
            st.markdown(f"- {hipotesis}")
    else:
        st.markdown("_Ninguna hipótesis se activó._")

    st.markdown("**Razón:**")
    st.info(resultado["razon"])

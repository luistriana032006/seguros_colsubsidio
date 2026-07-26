"""Métricas de los pesos entrenados -- compartido entre dashboard_pesos.py y app.py.

No genera datos -- scripts/entrenar_motor.py es quien calcula y escribe los pesos
(peso = soporte / total_producto, con floor 0.05, señal mínima 0.01 sin datos, y
ajuste aditivo para hipótesis como bucaramanga_mascota). Este módulo solo lee
data/modelos/pesos_hipotesis.json y, si existe, pesos_hipotesis_anterior.json.

render_pesos() no llama a st.set_page_config() ni a st.stop() -- usa return, para
poder vivir dentro de una pestaña de otra página sin cortarle el resto del script.
"""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from comun.colores import AZUL
from comun.zona_horaria import ZONA_COLOMBIA

RAIZ = Path(__file__).resolve().parent.parent  # dashboards/pesos.py -> raíz del repo
RUTA_PESOS = RAIZ / "data" / "modelos" / "pesos_hipotesis.json"
RUTA_PESOS_ANTERIOR = RAIZ / "data" / "modelos" / "pesos_hipotesis_anterior.json"

UMBRAL_ALTO = 0.7
UMBRAL_MEDIO = 0.4
PESO_DEBIL = 0.3
SOPORTE_DEBIL = 10


@st.cache_data(ttl=30)
def cargar_pesos(ruta):
    """Lee un JSON de pesos. None si el archivo no existe."""
    if not ruta.exists():
        return None
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def _aplanar(datos):
    """dict necesidad->clave->info a un DataFrame de una fila por hipótesis."""
    filas = []
    for necesidad, hipotesis_necesidad in datos.get("pesos", {}).items():
        for clave, info in hipotesis_necesidad.items():
            filas.append({
                "necesidad": necesidad,
                "hipotesis": clave,
                "peso": info["peso"],
                "soporte": info["soporte"],
                "total_producto": info["total_producto"],
                "productos": ", ".join(info.get("productos", [])),
            })
    return pd.DataFrame(filas)


def _nivel(peso):
    if peso >= UMBRAL_ALTO:
        return "🟢 Alto"
    if peso >= UMBRAL_MEDIO:
        return "🟡 Medio"
    return "🔴 Bajo"


def _fecha_legible(fecha_iso):
    """fecha_entrenamiento se guarda en UTC (ver scripts/entrenar_motor.py) -- se
    muestra convertida a hora de Colombia para que no confunda."""
    try:
        fecha_utc = datetime.fromisoformat(fecha_iso)
        fecha_colombia = fecha_utc.astimezone(ZONA_COLOMBIA)
        return fecha_colombia.strftime("%Y-%m-%d %H:%M") + " (Colombia)"
    except (TypeError, ValueError):
        return fecha_iso or "desconocida"


def _activar_autorefresco():
    try:
        from streamlit_autorefresh import st_autorefresh

        st_autorefresh(interval=30000, limit=None, key="pesos_autorefresh")
    except ImportError:
        import streamlit.components.v1 as components

        components.html(
            "<script>setTimeout(function(){window.location.reload();}, 30000);</script>",
            height=0,
        )


def render_pesos():
    """Dibuja las 5 secciones de pesos en la página actual.

    Dos formas de ver pesos nuevos sin matar el proceso: (1) si algo externo
    reentrena (otra terminal, el bot, un cron futuro), el auto-refresco de 30s
    + el cache_data(ttl=30) de cargar_pesos() lo recogen solos en <=30s. (2) el
    botón "Reentrenar ahora" de acá abajo corre scripts/entrenar_motor.py en
    este mismo proceso y refresca al toque, sin terminal ni reinicio.
    """
    _activar_autorefresco()

    col_refrescar, col_reentrenar = st.columns([1, 2])
    with col_refrescar:
        if st.button("Refrescar ahora", key="pesos_refrescar"):
            cargar_pesos.clear()
    with col_reentrenar:
        if st.button("🔄 Reentrenar ahora (recalcula con los datos actuales)", key="pesos_reentrenar"):
            try:
                with st.spinner("Recalculando pesos con los datos sintéticos + reales actuales..."):
                    from scripts.entrenar_motor import entrenar as _entrenar

                    _entrenar()
                cargar_pesos.clear()
                st.success("Pesos recalculados.")
                st.rerun()
            except Exception as error:
                st.error(f"No se pudo reentrenar: {error}")

    datos = cargar_pesos(RUTA_PESOS)

    if datos is None:
        st.info("No hay modelo entrenado. Corre: python3 scripts/entrenar_motor.py (o el botón de arriba).")
        return

    tabla = _aplanar(datos)

    # --- Sección 1: encabezado ---
    st.header("1. Encabezado")

    col1, col2, col3 = st.columns(3)
    col1.metric("Último entrenamiento", _fecha_legible(datos.get("fecha_entrenamiento")))
    col2.metric("Registros de entrenamiento", datos.get("total_registros_entrenamiento", "?"))
    col3.metric("Hipótesis activas", len(tabla))

    # --- Sección 2: pesos por necesidad ---
    st.header("2. Pesos por necesidad")

    necesidades = list(datos.get("pesos", {}).keys())
    tabs = st.tabs([n.capitalize() for n in necesidades])
    for tab, necesidad in zip(tabs, necesidades):
        with tab:
            df_n = tabla[tabla["necesidad"] == necesidad].copy()
            df_n["nivel"] = df_n["peso"].apply(_nivel)
            df_n = df_n.sort_values("peso", ascending=False)
            st.dataframe(
                df_n[["hipotesis", "peso", "nivel", "soporte", "total_producto"]].rename(columns={
                    "hipotesis": "Hipótesis", "peso": "Peso actual", "nivel": "Nivel",
                    "soporte": "Soporte", "total_producto": "Total producto",
                }),
                column_config={
                    "Peso actual": st.column_config.ProgressColumn(
                        "Peso actual", format="%.4f", min_value=-0.3, max_value=1.0,
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )

    # --- Sección 3: ranking global ---
    st.header("3. Ranking global — top 10 pesos más altos")

    top10 = tabla.sort_values("peso", ascending=False).head(10).sort_values("peso", ascending=True)
    etiquetas_top10 = [f"{fila.necesidad}.{fila.hipotesis}" for fila in top10.itertuples()]
    fig_top10 = px.bar(
        x=top10["peso"], y=etiquetas_top10, orientation="h",
        labels={"x": "Peso", "y": "Hipótesis"},
    )
    fig_top10.update_traces(marker_color=AZUL)
    st.plotly_chart(fig_top10, use_container_width=True)

    # --- Sección 4: hipótesis débiles ---
    st.header("4. Hipótesis débiles")

    debiles = tabla[(tabla["peso"] < PESO_DEBIL) | (tabla["soporte"] < SOPORTE_DEBIL)].sort_values("peso")
    if debiles.empty:
        st.success("Ninguna hipótesis está por debajo de los umbrales de confiabilidad (peso < 0.3 o soporte < 10).")
    else:
        st.warning("Estas hipótesis necesitan más datos para ser confiables")
        st.dataframe(
            debiles[["necesidad", "hipotesis", "peso", "soporte", "total_producto"]].rename(columns={
                "necesidad": "Necesidad", "hipotesis": "Hipótesis", "peso": "Peso",
                "soporte": "Soporte", "total_producto": "Total producto",
            }),
            hide_index=True,
            use_container_width=True,
        )

    # --- Sección 5: comparación antes vs después ---
    st.header("5. Comparación antes vs después")

    datos_anterior = cargar_pesos(RUTA_PESOS_ANTERIOR)

    if datos_anterior is None:
        st.info("Aún no hay entrenamiento anterior para comparar.\n\nCorre un reentrenamiento para ver los cambios.")
        return

    tabla_anterior = _aplanar(datos_anterior)[["necesidad", "hipotesis", "peso"]].rename(
        columns={"peso": "peso_anterior"}
    )
    comparacion = tabla[["necesidad", "hipotesis", "peso"]].rename(columns={"peso": "peso_actual"}).merge(
        tabla_anterior, on=["necesidad", "hipotesis"], how="outer"
    )
    comparacion["peso_actual"] = comparacion["peso_actual"].fillna(0.0)
    comparacion["peso_anterior"] = comparacion["peso_anterior"].fillna(0.0)
    comparacion["diferencia"] = comparacion["peso_actual"] - comparacion["peso_anterior"]

    def _flecha(diferencia):
        if diferencia > 0.0001:
            return f"↑ +{diferencia:.4f}"
        if diferencia < -0.0001:
            return f"↓ {diferencia:.4f}"
        return "→ 0.0000"

    comparacion["cambio"] = comparacion["diferencia"].apply(_flecha)
    comparacion = comparacion.sort_values("diferencia", ascending=False)

    def _color_cambio(valor):
        if valor.startswith("↑"):
            return "color: #2ecc71; font-weight: bold"
        if valor.startswith("↓"):
            return "color: #e74c3c; font-weight: bold"
        return "color: gray"

    tabla_comparacion = comparacion[
        ["necesidad", "hipotesis", "peso_anterior", "peso_actual", "cambio"]
    ].rename(columns={
        "necesidad": "Necesidad", "hipotesis": "Hipótesis",
        "peso_anterior": "Peso anterior", "peso_actual": "Peso actual", "cambio": "Cambio",
    })
    st.dataframe(
        tabla_comparacion.style.map(_color_cambio, subset=["Cambio"]),
        hide_index=True,
        use_container_width=True,
    )

"""Dashboard de calidad del aire global (Fase II).

Ejecutar desde la raíz del repo:  streamlit run app/streamlit_app.py
"""

import sys
from dataclasses import replace
from pathlib import Path

import streamlit as st

# `streamlit run` ya agrega esta carpeta al path; AppTest (tests) no.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from air_quality import cargar_procesado  # noqa: E402
from air_quality.metricas import filtrar

import componentes as ui
import filtros
import tema
from capitulos import causa, diagnostico, patrones

st.set_page_config(page_title="Calidad del aire global · Dashboard", page_icon=":material/air:",
                   layout="wide", initial_sidebar_state="collapsed")
tema.registrar_plantillas()


@st.cache_data(show_spinner=False)
def datos():
    return cargar_procesado()


df_total = datos()
filtros.inicializar(df_total)
st.session_state.setdefault("oscuro", False)
t = tema.tema(st.session_state["oscuro"])
ui.html(f"<style>{tema.css(t)}</style>")

_, c_modo = st.columns([10, 1.6])
c_modo.toggle("Modo oscuro", key="oscuro")

ui.encabezado(len(df_total), df_total["City"].nunique(), df_total["Date"].min(), df_total["Date"].max())
ui.navegacion(disponibles=("01", "02", "03"))

f = filtros.barra(df_total)
df = filtrar(df_total, f)
# Contexto: mismos filtros salvo la ciudad. Las vistas comparativas muestran todas las ciudades y
# resaltan la seleccionada (foco + contexto) en lugar de quedarse con una sola barra.
df_contexto = filtrar(df_total, replace(f, ciudades=()))

diagnostico.render(df, df_contexto, df_total, f, t)
patrones.render(df, df_contexto, f, t)
causa.render(df, f, t)

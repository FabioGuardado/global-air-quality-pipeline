"""Dashboard de calidad del aire global (Fase II).

Ejecutar desde la raíz del repo:  streamlit run app/streamlit_app.py

Cada capítulo es una página (`st.navigation`). Este archivo dibuja lo común a todas: barra
lateral de filtros, cabecera, menú de capítulos y el enlace al siguiente capítulo.
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
import contexto
import filtros
import tema

st.set_page_config(page_icon=":material/air:",
                   layout="wide", initial_sidebar_state="expanded")
tema.registrar_plantillas()


@st.cache_data(show_spinner=False)
def datos():
    return cargar_procesado()


def _alternar_tema():
    st.session_state["oscuro"] = not st.session_state["oscuro"]


paginas = {num: st.Page(f"paginas/{ancla}.py", title=f"{num} {nombre} · Calidad del aire global",
                        url_path=ancla, default=num == "01")
           for num, ancla, nombre in ui.CAPITULOS + [ui.ANEXO]}
pagina = st.navigation(list(paginas.values()), position="hidden")
actual = next(num for num, p in paginas.items() if p.title == pagina.title)

df_total = datos()
filtros.inicializar(df_total)
st.session_state.setdefault("oscuro", False)
t = tema.tema(st.session_state["oscuro"])
ui.html(f"<style>{tema.css(t)}</style>")
# Logo arriba a la izquierda de la barra lateral; con la barra contraída queda solo el ícono,
# junto al botón para expandirla.
st.logo(tema.logo_svg(t), icon_image=tema.logo_svg(t, con_texto=False), size="large")
ui.traducir_widgets()

f = filtros.barra(df_total, paginas[ui.ANEXO[0]])
df = filtrar(df_total, f)
# Contexto: mismos filtros salvo la ciudad. Las vistas comparativas muestran todas las ciudades y
# resaltan la seleccionada (foco + contexto) en lugar de quedarse con una sola barra.
df_contexto = filtrar(df_total, replace(f, ciudades=()))
contexto.guardar(contexto.Contexto(df_total, df, df_contexto, f, t))
st.session_state["_activos"] = filtros.resumen_activo(f, df_total)

# --- Cabecera: marca + tema; completa solo en el capítulo 01 ---------------------------------
c_marca, c_tema = st.columns([12, 1], vertical_alignment="center")
with c_marca:
    ui.marca()
with c_tema:
    oscuro = st.session_state["oscuro"]
    st.button("Activar modo claro" if oscuro else "Activar modo oscuro", key="btn_tema",
              icon=":material/light_mode:" if oscuro else ":material/dark_mode:", type="tertiary",
              help="Cambiar a modo claro" if oscuro else "Cambiar a modo oscuro", on_click=_alternar_tema)
if actual == "01":
    ui.encabezado(len(df_total), df_total["City"].nunique(), df_total["Date"].min(), df_total["Date"].max())
ui.navegacion(paginas, actual)

pagina.run()

ui.siguiente(paginas, actual)

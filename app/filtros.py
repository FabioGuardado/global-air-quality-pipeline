"""Filtros globales sincronizados (barra lateral). Todo el estado vive en st.session_state con prefijo `f_`.

Los gráficos no filtran por su cuenta: escriben en este mismo estado (filtro cruzado) y la app
vuelve a ejecutarse con los filtros nuevos, así todas las vistas responden a la vez.
"""

from html import escape

import pandas as pd
import streamlit as st

from air_quality.config import CIUDADES, REGIONES
from air_quality.metricas import Filtros, nombre_ciudad
from air_quality.severidad import METAS_OMS, nombres_niveles

import componentes as ui

CONTAMINANTES = list(METAS_OMS)
ETIQUETA_CONT = {"PM2.5": "PM₂.₅", "PM10": "PM₁₀", "NO2": "NO₂"}


def _defaults(df):
    return {
        "f_fechas": (df["Date"].min().date(), df["Date"].max().date()),
        "f_regiones": [],
        "f_ciudades": [],
        "f_cont": "PM2.5",
        "f_niveles": [],
    }


def inicializar(df):
    for k, v in _defaults(df).items():
        st.session_state.setdefault(k, v)


def restablecer(df):
    for k, v in _defaults(df).items():
        st.session_state[k] = v


def _ciudades_de(regiones):
    return [c for c, (r, _, _) in CIUDADES.items() if not regiones or r in regiones]


def _al_cambiar_region():
    validas = set(_ciudades_de(st.session_state["f_regiones"]))
    st.session_state["f_ciudades"] = [c for c in st.session_state["f_ciudades"] if c in validas]


def _al_cambiar_contaminante():
    if not st.session_state["f_cont"]:          # el control permite deseleccionar
        st.session_state["f_cont"] = "PM2.5"
    # los nombres de nivel dependen del contaminante (el NO2 no tiene IT-3 ni IT-4)
    validos = set(nombres_niveles(st.session_state["f_cont"]))
    st.session_state["f_niveles"] = [n for n in st.session_state["f_niveles"] if n in validos]


def alternar_ciudad(ciudad):
    """Filtro cruzado desde un gráfico: selecciona solo esa ciudad, o la quita si ya lo estaba."""
    actual = st.session_state.get("f_ciudades", [])
    st.session_state["f_ciudades"] = [] if actual == [ciudad] else [ciudad]
    region = CIUDADES[ciudad][0]
    if st.session_state.get("f_regiones") and region not in st.session_state["f_regiones"]:
        st.session_state["f_regiones"] = []


def ciudad_de_seleccion(estado, indice_custom):
    """Extrae la ciudad del primer punto seleccionado en un plotly_chart (o None)."""
    try:
        puntos = estado["selection"]["points"]
    except (KeyError, TypeError):
        return None
    for p in puntos:
        custom = p.get("customdata")
        if custom is not None and len(custom) > indice_custom:
            return custom[indice_custom]
    return None


def barra(df):
    """Dibuja los filtros en la barra lateral y devuelve los `Filtros` activos."""
    minimo, maximo = df["Date"].min().date(), df["Date"].max().date()
    with st.sidebar:
        st.html('<div class="lateral-titulo">Filtros</div>'
                '<p class="lateral-sub">Se aplican a los cuatro capítulos.</p>')
        st.date_input("Periodo", key="f_fechas", min_value=minimo, max_value=maximo, format="DD/MM/YYYY")
        st.multiselect("Región", REGIONES, key="f_regiones", placeholder="Todas",
                       on_change=_al_cambiar_region)
        st.multiselect("Ciudad", _ciudades_de(st.session_state["f_regiones"]), key="f_ciudades",
                       format_func=nombre_ciudad, placeholder="Todas")
        st.segmented_control("Contaminante", CONTAMINANTES, key="f_cont", format_func=ETIQUETA_CONT.get,
                             on_change=_al_cambiar_contaminante, width="stretch")
        cont = st.session_state["f_cont"] or "PM2.5"
        st.multiselect("Severidad OMS", nombres_niveles(cont), key="f_niveles",
                       placeholder="Todos los niveles")
        st.button("Limpiar filtros", on_click=restablecer, args=(df,), width="stretch",
                  icon=":material/filter_alt_off:", key="btn_limpiar")
        st.html(f'<div class="lateral-pie">{len(df):,} mediciones · {df["City"].nunique()} ciudades<br>'
                f'Fuente: {ui.fuente()}</div>')

    fechas = st.session_state["f_fechas"]
    desde = pd.Timestamp(fechas[0]) if len(fechas) > 0 else None
    hasta = pd.Timestamp(fechas[1]) if len(fechas) > 1 else None
    return Filtros(desde=desde, hasta=hasta,
                   regiones=tuple(st.session_state["f_regiones"]),
                   ciudades=tuple(st.session_state["f_ciudades"]),
                   contaminante=cont, niveles=tuple(st.session_state["f_niveles"]))


def _fecha_corta(d):
    return d.strftime("%d/%m/%Y")


def resumen_activo(f: Filtros, df):
    """Línea "Vista: …" bajo el título de cada capítulo. Lo filtrado se resalta con el acento.

    Con la barra lateral contraída es la única pista de qué se está mirando.
    """
    def parte(texto, filtrado):
        return f'<b class="on">{escape(texto)}</b>' if filtrado else escape(texto)

    partes = [parte(ETIQUETA_CONT[f.contaminante], f.contaminante != "PM2.5")]
    if f.ciudades:
        partes.append(parte(", ".join(nombre_ciudad(c) for c in f.ciudades), True))
    elif f.regiones:
        partes.append(parte(", ".join(f.regiones), True))
    else:
        partes.append(parte(f"{df['City'].nunique()} ciudades", False))
    completo = ((f.desde is None or f.desde <= df["Date"].min()) and
                (f.hasta is None or f.hasta >= df["Date"].max()))
    if completo:
        partes.append(parte("todo el periodo", False))
    else:
        desde = f.desde or df["Date"].min()
        hasta = f.hasta or desde
        partes.append(parte(f"{_fecha_corta(desde)} – {_fecha_corta(hasta)}", True))
    if f.niveles:
        partes.append(parte(", ".join(f.niveles), True))
    return f'<div class="activos"><span>Vista</span>{" · ".join(partes)}</div>'


def hay_filtros(f: Filtros, df):
    completo = (f.desde == df["Date"].min() or f.desde is None) and \
               (f.hasta == df["Date"].max() or f.hasta is None)
    return not completo or bool(f.regiones or f.ciudades or f.niveles)


def describir(f: Filtros):
    """Resumen legible de los filtros activos (para los títulos dinámicos)."""
    partes = []
    if f.ciudades:
        partes.append(", ".join(nombre_ciudad(c) for c in f.ciudades))
    elif f.regiones:
        partes.append(", ".join(f.regiones))
    if f.niveles:
        partes.append("nivel " + ", ".join(f.niveles).lower())
    return " · ".join(partes)

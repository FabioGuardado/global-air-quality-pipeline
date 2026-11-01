"""Filtros globales sincronizados. Todo el estado vive en st.session_state con prefijo `f_`.

Los gráficos no filtran por su cuenta: escriben en este mismo estado (filtro cruzado) y la app
vuelve a ejecutarse con los filtros nuevos, así todas las vistas responden a la vez.
"""

import pandas as pd
import streamlit as st

from air_quality.config import CIUDADES, REGIONES
from air_quality.metricas import Filtros, nombre_ciudad
from air_quality.severidad import METAS_OMS, nombres_niveles

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
    """Dibuja la fila de filtros y devuelve los `Filtros` activos."""
    minimo, maximo = df["Date"].min().date(), df["Date"].max().date()
    with st.container(key="barra-filtros"):
        c_fecha, c_reg, c_ciu, c_cont, c_niv, c_reset = st.columns([2.1, 1.9, 2.2, 2.3, 2.2, 1.0],
                                                                   vertical_alignment="bottom")
        c_fecha.date_input("Periodo", key="f_fechas", min_value=minimo, max_value=maximo,
                           format="DD/MM/YYYY")
        c_reg.multiselect("Región", REGIONES, key="f_regiones", placeholder="Todas",
                          on_change=_al_cambiar_region)
        c_ciu.multiselect("Ciudad", _ciudades_de(st.session_state["f_regiones"]), key="f_ciudades",
                          format_func=nombre_ciudad, placeholder="Todas")
        c_cont.segmented_control("Contaminante", CONTAMINANTES, key="f_cont",
                                 format_func=ETIQUETA_CONT.get, on_change=_al_cambiar_contaminante)
        cont = st.session_state["f_cont"] or "PM2.5"
        c_niv.multiselect("Severidad OMS", nombres_niveles(cont), key="f_niveles",
                          placeholder="Todos los niveles")
        c_reset.button("Limpiar", on_click=restablecer, args=(df,), use_container_width=True,
                       help="Quitar todos los filtros")

    fechas = st.session_state["f_fechas"]
    desde = pd.Timestamp(fechas[0]) if len(fechas) > 0 else None
    hasta = pd.Timestamp(fechas[1]) if len(fechas) > 1 else None
    return Filtros(desde=desde, hasta=hasta,
                   regiones=tuple(st.session_state["f_regiones"]),
                   ciudades=tuple(st.session_state["f_ciudades"]),
                   contaminante=cont, niveles=tuple(st.session_state["f_niveles"]))


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

"""Datos y filtros de la ejecución actual, compartidos entre el punto de entrada y las páginas.

`streamlit_app.py` arma el contexto (datos, filtros de la barra lateral y tema) y lo guarda en
`st.session_state`, que es propio de cada sesión. Cada archivo de `paginas/` solo lo lee y
dibuja su capítulo.
"""

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from air_quality.metricas import Filtros

_CLAVE = "_contexto"


@dataclass(frozen=True)
class Contexto:
    df_total: pd.DataFrame       # dataset completo
    df: pd.DataFrame             # todos los filtros aplicados
    df_contexto: pd.DataFrame    # todos los filtros salvo la ciudad (foco + contexto)
    f: Filtros
    t: object                    # tema.Tema


def guardar(ctx: Contexto):
    st.session_state[_CLAVE] = ctx


def actual() -> Contexto:
    return st.session_state[_CLAVE]

"""Lectura de los datasets crudo y procesado."""

import pandas as pd

from .config import PROCESSED_PATH, RAW_PATH, REGIONES


def cargar_crudo(path=RAW_PATH):
    return pd.read_csv(path)


def cargar_procesado(path=PROCESSED_PATH):
    """CSV entregable con tipos restaurados (Date como fecha, City/Country como categoría)."""
    df = pd.read_csv(path, parse_dates=["Date"])
    for c in ["City", "Country", "trimestre_met"]:
        df[c] = df[c].astype("category")
    df["region"] = pd.Categorical(df["region"], categories=REGIONES, ordered=True)
    df["fin_semana"] = df["fin_semana"].astype(bool)
    return df

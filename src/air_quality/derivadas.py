"""Fase IV (1): variables derivadas."""

import numpy as np
import pandas as pd

from .config import ORDEN_VIENTO, TRIMESTRE, UMBRALES_OMS


def agregar_derivadas(df, umbrales=UMBRALES_OMS):
    """Agrega las derivadas físicas, de severidad, de tendencia y temporales.

    Requiere `mes` y `dia_semana` (ver `limpieza.agregar_variables_tiempo`).
    """
    df = df.copy(deep=True).sort_values(["City", "Date"])

    # Fracción fina: PM2.5 es un subconjunto de PM10, el ratio debería caer en (0, 1]
    df["ratio_pm"] = df["PM2.5"] / df["PM10"]
    df["ratio_pm_imposible"] = df["ratio_pm"] > 1

    # Severidad: cuántas guías OMS supera la fila
    df["n_excedencias_oms"] = sum((df[c] > u).astype(int) for c, u in umbrales.items())

    # Nivel base de la ciudad vs. el día concreto
    df["pm25_vs_ciudad"] = df["PM2.5"] - df.groupby("City")["PM2.5"].transform("median")

    # Tendencia local: ventana de 7 días reales. El frame está ordenado por City y Date,
    # así que la serie devuelta se alinea posición a posición.
    df["pm25_movil_7d"] = (df.set_index("Date").groupby("City")["PM2.5"]
                           .rolling("7D").mean().values)
    df["pm25_delta"] = df.groupby("City")["PM2.5"].diff().fillna(0)

    # Descomposición temporal (las cíclicas evitan que diciembre y enero queden a 11 de distancia)
    df["trimestre_met"] = df["mes"].map(TRIMESTRE)
    df["mes_sin"] = np.sin(2 * np.pi * df["mes"] / 12)
    df["mes_cos"] = np.cos(2 * np.pi * df["mes"] / 12)
    df["dia_sem_sin"] = np.sin(2 * np.pi * df["dia_semana"] / 7)
    df["dia_sem_cos"] = np.cos(2 * np.pi * df["dia_semana"] / 7)
    return df


def agregar_ordinales(df):
    """viento_ord (0-3) desde viento_cat y fin_semana como entero."""
    df = df.copy()
    df["viento_ord"] = pd.Categorical(df["viento_cat"], categories=ORDEN_VIENTO,
                                      ordered=True).codes
    df["fin_semana_int"] = df["fin_semana"].astype(int)
    return df

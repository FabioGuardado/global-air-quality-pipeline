"""Fase IV (2 y 3): codificación, multicolinealidad y escalado."""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

from .bitacora import _registrar
from .outliers import flags_outliers


def dummies_ciudad(df, drop_first=True):
    return pd.get_dummies(df["City"], prefix="city", drop_first=drop_first, dtype=int)


def vif(X):
    """Factor de inflación de la varianza de cada columna frente al resto."""
    X = X.astype(float)
    resultado = {}
    for c in X.columns:
        A = np.column_stack([np.ones(len(X)), X.drop(columns=c).values])
        coef, *_ = np.linalg.lstsq(A, X[c].values, rcond=None)
        resid = X[c].values - A @ coef
        ss_tot = ((X[c].values - X[c].mean()) ** 2).sum()
        r2 = 1 - resid @ resid / ss_tot if ss_tot > 0 else 0.0
        resultado[c] = np.inf if r2 >= 1 else 1 / (1 - r2)
    return pd.Series(resultado).sort_values(ascending=False)


ESCALADORES = {"MinMaxScaler": MinMaxScaler,
               "StandardScaler": StandardScaler,
               "RobustScaler": RobustScaler}

MOTIVOS = {
    "RobustScaler": "colas pesadas: la mediana y el IQR aguantan donde la media y el rango no",
    "MinMaxScaler": "sin colas pesadas y con rango acotado y estable (p99 ≈ max)",
    "StandardScaler": "sin colas pesadas pero con rango abierto",
}


def diagnostico_escalado(df, cols):
    """Indicadores de colas y rango por columna, con el escalador elegido."""
    diag = pd.DataFrame({
        "skew": df[cols].skew(),
        "curtosis": df[cols].kurt(),
        "IQR/std": (df[cols].quantile(.75) - df[cols].quantile(.25)) / df[cols].std(),
        "% outliers": [(flags_outliers(df[c]).sum(axis=1) >= 2).mean() * 100 for c in cols],
        "p99/max": df[cols].quantile(.99) / df[cols].max(),
    }).round(3)
    diag["escalador"] = diag.apply(elegir_escalador, axis=1)
    return diag


def elegir_escalador(fila):
    if fila["% outliers"] > 5 or fila["IQR/std"] < 1.0:
        return "RobustScaler"
    if abs(fila["p99/max"]) > 0.9:
        return "MinMaxScaler"
    return "StandardScaler"


def escalar(df, diag, bitacora=None):
    """Ajusta y aplica a cada grupo de columnas el escalador que le asignó `diag`."""
    escalado = pd.DataFrame(index=df.index, columns=list(diag.index), dtype=float)
    for nombre, grupo in diag.groupby("escalador"):
        cols = list(grupo.index)
        escalado[cols] = ESCALADORES[nombre]().fit_transform(df[cols])
        _registrar(bitacora, "IV", ", ".join(cols), f"Escalar con {nombre}", MOTIVOS[nombre])
    return escalado

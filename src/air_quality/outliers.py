"""Fase III: detección de outliers univariada (IQR, Z, MAD) y multivariada (Mahalanobis)."""

import pandas as pd
from scipy import stats
from sklearn.covariance import MinCovDet

from .config import RANDOM_STATE


def flags_outliers(s):
    """Una columna booleana por criterio."""
    q1, q3 = s.quantile([.25, .75])
    iqr = q3 - q1
    mad = stats.median_abs_deviation(s.dropna())
    return pd.DataFrame({
        "IQR": (s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr),
        "Z": ((s - s.mean()) / s.std()).abs() > 3,
        "MAD": (0.6745 * (s - s.median()) / mad).abs() > 3.5 if mad else False,
    })


def consenso_outliers(df, cols, min_criterios=2):
    """Outlier de consenso: lo marcan al menos `min_criterios` de los tres criterios."""
    return pd.DataFrame({c: flags_outliers(df[c]).sum(axis=1) >= min_criterios for c in cols})


def resumen_outliers(df, cols, min_criterios=2):
    filas = {}
    for c in cols:
        f = flags_outliers(df[c])
        consenso = f.sum(axis=1) >= min_criterios
        filas[c] = {**f.sum().to_dict(),
                    f"consenso (>={min_criterios})": int(consenso.sum()),
                    "% consenso": round(consenso.mean() * 100, 2)}
    return pd.DataFrame(filas).T


def outliers_mahalanobis(df, cols, alpha=0.999, random_state=RANDOM_STATE):
    """Distancia de Mahalanobis robusta (MCD) contra el cuantil chi² de `alpha`."""
    datos = df[cols].dropna()
    d2 = MinCovDet(random_state=random_state).fit(datos).mahalanobis(datos)
    return pd.Series(d2 > stats.chi2.ppf(alpha, df=len(cols)), index=datos.index)

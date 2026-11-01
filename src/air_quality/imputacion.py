"""Fase III: diagnóstico de nulos, elección de estrategia e imputación por ciudad."""

import pandas as pd
from scipy import stats

from .bitacora import _registrar
from .config import NUM


def columnas_con_nulos(df, cols=NUM):
    return [c for c in cols if c in df.columns and df[c].isna().any()]


def plan_imputacion(data, cols, ref_cols=NUM):
    """Elige una estrategia por columna a partir del % de nulos, el mecanismo y la forma.

    - `vars_sig_MAR`: variables de `cols` cuya distribución cambia (Mann-Whitney, p<0.05)
      entre filas con y sin nulo en la columna: señal de MAR.
    - `r_max`: mayor |Spearman| con el resto de `ref_cols`.
    """
    ref_cols = [c for c in ref_cols if c in data.columns]
    corr_num = data[ref_cols].corr("spearman").abs()
    filas = []
    for c in cols:
        s = data[c]
        pct = s.isna().mean() * 100
        ind = s.isna()
        n_sig = sum(stats.mannwhitneyu(data.loc[ind, o].dropna(),
                                       data.loc[~ind, o].dropna()).pvalue < 0.05
                    for o in cols if o != c and data.loc[ind, o].notna().sum() > 5)
        r_max = corr_num[c].drop(c).max()
        if pct > 60:
            est, motivo = "eliminar_columna", f"{pct:.0f}% de nulos"
        elif r_max > 0.5 and n_sig >= 2:
            est, motivo = "revisar_multivariada", f"MAR probable (r_max={r_max:.2f})"
        elif pct < 5:
            est, motivo = "interpolacion", f"{pct:.1f}% de nulos en serie diaria por ciudad"
        elif abs(s.skew()) > 1:
            est, motivo = "mediana_ciudad", f"skew={s.skew():.2f} (sesgada)"
        else:
            est, motivo = "media_ciudad", f"skew={s.skew():.2f} (simétrica)"
        filas.append({"columna": c, "pct_nulos": round(pct, 2), "vars_sig_MAR": n_sig,
                      "r_max": round(r_max, 3), "estrategia": est, "motivo": motivo})
    return pd.DataFrame(filas, columns=["columna", "pct_nulos", "vars_sig_MAR", "r_max",
                                        "estrategia", "motivo"]).set_index("columna")


# Cada imputador devuelve la serie de valores de reemplazo, calculada por ciudad.
IMPUTADORES = {
    "interpolacion": lambda d, c: d.groupby("City")[c].transform(
        lambda s: s.interpolate(limit=3, limit_direction="both")),
    "mediana_ciudad": lambda d, c: d.groupby("City")[c].transform("median"),
    "media_ciudad": lambda d, c: d.groupby("City")[c].transform("mean"),
}


def aplicar_imputacion(df, plan, bitacora=None):
    """Aplica el plan. Lo que el método por ciudad no cubre se rellena con la mediana global."""
    df = df.copy()
    for c, fila in plan.iterrows():
        if fila["estrategia"] == "eliminar_columna":
            df = df.drop(columns=c)
            _registrar(bitacora, "III-nulos", c, "Eliminar columna", fila["motivo"])
            continue
        if fila["estrategia"] not in IMPUTADORES:
            raise ValueError(f"Estrategia sin imputador automático para {c}: "
                             f"{fila['estrategia']}")
        n = int(df[c].isna().sum())
        df[c] = (df[c]
                 .fillna(IMPUTADORES[fila["estrategia"]](df, c))
                 .fillna(df[c].median()))
        _registrar(bitacora, "III-nulos", c, f"{fila['estrategia']} ({n} valores)",
                   fila["motivo"])
    return df


def validar_imputacion(antes, despues, cols):
    """Compara media, std y distribución (KS) antes y después de imputar."""
    v = pd.DataFrame({
        "media_antes": antes[cols].mean(),
        "media_despues": despues[cols].mean(),
        "std_antes": antes[cols].std(),
        "std_despues": despues[cols].std(),
        "KS_p": [stats.ks_2samp(antes[c].dropna(), despues[c]).pvalue for c in cols],
    }).round(3)
    v["distribucion_intacta"] = v["KS_p"] > 0.05
    return v

"""Auditoría del dato: qué hizo el pipeline con el CSV crudo y si los datos salieron intactos.

Todo se calcula con las mismas funciones del pipeline (no se reimplementa la limpieza), así las
cifras de la página de auditoría no pueden desalinearse del CSV procesado.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from .config import CLAVES, NUM, POLL
from .limpieza import eliminar_duplicados, normalizar_claves
from .pipeline import ejecutar

ALFA_KS = 0.05
TOPE_DELTA_SPEARMAN = 0.05     # |Δρ| por debajo de esto se considera que la correlación no cambió


@dataclass(frozen=True)
class Auditoria:
    resumen: dict                 # cifras del antes → después
    embudo: pd.DataFrame          # etapa, filas
    distribuciones: pd.DataFrame  # una fila por variable: medias, std, Δ %, KS
    verificaciones: pd.DataFrame  # control, aprobado, detalle, capitulo
    bitacora: pd.DataFrame        # fase, columna, accion, justificacion
    nulos_ciudad: pd.Series       # % de nulos por ciudad × contaminante en el crudo


def _numerico(df, cols):
    return df[cols].apply(pd.to_numeric, errors="coerce")


def comparar_distribuciones(antes, despues, cols):
    """Media, desviación y prueba KS de cada variable antes y después del pipeline."""
    a, d = _numerico(antes, cols), _numerico(despues, cols)
    r = pd.DataFrame({
        "variable": cols,
        "media_antes": a.mean().values, "media_despues": d.mean().values,
        "std_antes": a.std().values, "std_despues": d.std().values,
        "ks_p": [stats.ks_2samp(a[c].dropna(), d[c].dropna()).pvalue for c in cols],
    })
    r["delta_media_pct"] = (r["media_despues"] / r["media_antes"] - 1) * 100
    r["delta_std_pct"] = (r["std_despues"] / r["std_antes"] - 1) * 100
    r["intacta"] = r["ks_p"] > ALFA_KS
    return r


def delta_spearman(antes, despues, cols):
    """Mayor cambio absoluto en la correlación de Spearman entre cualquier par de variables."""
    ra = _numerico(antes, cols).corr("spearman")
    rd = _numerico(despues, cols).corr("spearman")
    return float((rd - ra).abs().to_numpy().max())


def verificar(procesado, distribuciones, max_delta_rho):
    """Lista de controles de calidad sobre el CSV procesado. Un control que falla se reporta tal cual."""
    n_dup = int(procesado.duplicated(subset=CLAVES).sum())
    n_nulos = int(procesado.isna().sum().sum())
    n_ok = int(distribuciones["intacta"].sum())
    pct_imp = float((procesado["PM2.5"] > procesado["PM10"]).mean() * 100)
    filas = [
        ("Claves únicas", n_dup == 0,
         "Ninguna ciudad repite fecha" if n_dup == 0 else f"{n_dup} claves repetidas", None),
        ("Sin valores nulos", n_nulos == 0,
         "Todas las celdas tienen valor" if n_nulos == 0 else f"{n_nulos} celdas vacías", None),
        ("Distribuciones preservadas", n_ok == len(distribuciones),
         f"Prueba KS sin diferencia en {n_ok} de {len(distribuciones)} variables (p > {ALFA_KS})", None),
        ("Correlaciones intactas", max_delta_rho < TOPE_DELTA_SPEARMAN,
         f"Cambio máximo en la correlación de Spearman: {max_delta_rho:.3f}", None),
        ("Coherencia física de los sensores", pct_imp == 0,
         f"{pct_imp:.1f} % de las lecturas tiene PM2.5 > PM10, algo imposible" if pct_imp else
         "PM2.5 nunca supera a PM10", "02"),
    ]
    return pd.DataFrame(filas, columns=["control", "aprobado", "detalle", "capitulo"])


def auditar(df_raw, resultado=None):
    """Audita el pipeline completo sobre el CSV crudo (`resultado` evita re-ejecutarlo si ya se tiene)."""
    resultado = resultado if resultado is not None else ejecutar(df_raw)
    procesado = resultado.procesado
    claves = normalizar_claves(df_raw)
    sin_exactos = claves.drop_duplicates()
    sin_duplicados = eliminar_duplicados(claves)

    cols = [c for c in NUM if c in procesado.columns]
    distribuciones = comparar_distribuciones(claves, procesado, cols)
    max_rho = delta_spearman(claves, procesado, cols)

    nulos_crudo = int(df_raw.isna().sum().sum())
    nulos_imputados = int(sin_duplicados[cols].isna().sum().sum())
    resumen = dict(
        filas_crudo=len(df_raw), filas_procesado=len(procesado),
        duplicados_exactos=len(claves) - len(sin_exactos),
        duplicados_clave=len(sin_exactos) - len(sin_duplicados),
        variantes_ciudad=int(df_raw["City"].nunique()), ciudades=int(procesado["City"].nunique()),
        nulos_crudo=nulos_crudo, nulos_imputados=nulos_imputados,
        nulos_con_duplicados=nulos_crudo - nulos_imputados,
        nulos_procesado=int(procesado.isna().sum().sum()),
        decisiones=len(resultado.bitacora), delta_spearman=max_rho,
    )
    resumen["duplicados"] = resumen["duplicados_exactos"] + resumen["duplicados_clave"]
    embudo = pd.DataFrame({
        # la imputación y las derivadas no quitan filas: lo que sale de duplicados es el procesado
        "etapa": ["CSV crudo", "Sin exactos", "Sin repetir clave"],
        "filas": [len(df_raw), len(sin_exactos), len(sin_duplicados)],
    })
    nulos_ciudad = (claves.groupby("City")[[c for c in POLL if c in claves.columns]]
                    .apply(lambda d: d.isna().mean() * 100).stack())
    return Auditoria(resumen=resumen, embudo=embudo, distribuciones=distribuciones,
                     verificaciones=verificar(procesado, distribuciones, max_rho),
                     bitacora=resultado.bitacora.to_frame(), nulos_ciudad=nulos_ciudad)


def rango(serie):
    """(mínimo, mediana, máximo) de una serie, para describir dispersión en una frase."""
    if serie.empty:
        return (np.nan, np.nan, np.nan)
    return (float(serie.min()), float(serie.median()), float(serie.max()))

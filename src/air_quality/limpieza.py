"""Fase I y III: perfilado, saneamiento de claves y duplicados."""

import re
import unicodedata

import pandas as pd

from .bitacora import _registrar
from .config import CLAVES, FORMATO_FECHA, ORDEN_VIENTO


def tipo_por_cardinalidad(s):
    n = s.nunique(dropna=True)
    if n <= 1:                            return "constante"
    if n / len(s) > 0.95:                 return "posible identificador"
    if n <= 10:                           return "baja cardinalidad"
    if pd.api.types.is_numeric_dtype(s):  return "numérica continua"
    return "alta cardinalidad"


def perfilar(df):
    """Tipo, cardinalidad, nulos y rol de cada columna en una sola tabla."""
    return pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "n_unicos": df.nunique(),
        "pct_unicos": (df.nunique() / len(df) * 100).round(2),
        "n_nulos": df.isna().sum(),
        "pct_nulos": (df.isna().mean() * 100).round(2),
        "categoria": df.apply(tipo_por_cardinalidad),
    })


def normalizar_texto(s):
    """Sin acentos, sin espacios sobrantes, en minúsculas."""
    if pd.isna(s):
        return s
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("utf-8")
    return re.sub(r"\s+", " ", s).strip().lower()


def fechas_invalidas(fechas, fmt):
    """Cuántas fechas no se pueden parsear con `fmt` (sirve para elegir el formato)."""
    return int(pd.to_datetime(fechas, format=fmt, errors="coerce").isna().sum())


def normalizar_claves(df, bitacora=None):
    """Normaliza City y Country y parsea Date. Devuelve una copia."""
    original = df
    df = df.copy(deep=True)
    for c in ["City", "Country"]:
        df[c] = df[c].map(normalizar_texto)
        _registrar(bitacora, "I-claves", c, "Normalizar texto",
                   f"{original[c].nunique()} variantes por mayúsculas/espacios → "
                   f"{df[c].nunique()} reales")

    alternativa = fechas_invalidas(original["Date"], "%d/%m/%Y")
    df["Date"] = pd.to_datetime(df["Date"], format=FORMATO_FECHA, errors="coerce")
    _registrar(bitacora, "I-claves", "Date", f"Parsear con formato {FORMATO_FECHA}",
               f"{df['Date'].isna().sum()} fechas inválidas (con %d/%m/%Y serían {alternativa})")
    return df


def agregar_variables_tiempo(df):
    """mes, dia_semana (0=lunes) y fin_semana a partir de Date."""
    df = df.copy()
    df["mes"] = df["Date"].dt.month
    df["dia_semana"] = df["Date"].dt.dayofweek
    df["fin_semana"] = df["dia_semana"] >= 5
    return df


def agregar_viento_cat(df):
    """Cuartiles de Wind Speed como categoría ordenada."""
    df = df.copy()
    df["viento_cat"] = pd.qcut(df["Wind Speed"], 4, labels=ORDEN_VIENTO)
    return df


def eliminar_duplicados(df, claves=CLAVES, bitacora=None):
    """Quita duplicados exactos y luego los de clave de negocio.

    De cada clave repetida se conserva el registro con más columnas no nulas.
    """
    df = df.copy(deep=True).sort_values(["City", "Date"]).reset_index(drop=True)

    n_exactos = int(df.duplicated().sum())
    df = df.drop_duplicates()
    _registrar(bitacora, "III-duplicados", "todas", f"Eliminar {n_exactos} filas",
               "Registros idénticos en todas las columnas")

    n_parciales = int(df.duplicated(subset=claves).sum())
    df = (df.assign(_completitud=df.notna().sum(axis=1))
            .sort_values("_completitud", ascending=False)
            .drop_duplicates(subset=claves, keep="first")
            .drop(columns="_completitud")
            .sort_index())
    _registrar(bitacora, "III-duplicados", "+".join(claves), f"Eliminar {n_parciales} filas",
               "Misma clave de negocio: se conserva el registro más completo")
    return df

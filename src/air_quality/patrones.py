"""Métricas del capítulo 02: patrones temporales, episodios e integridad del sensor."""

import numpy as np
import pandas as pd

from .severidad import guia

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def serie_movil(df, contaminante, ventana="7D", min_periodos=3):
    """Media móvil de `ventana` días reales por ciudad (los huecos no se rellenan)."""
    if df.empty:
        return pd.DataFrame(columns=["City", "Date", "valor", "movil"])
    partes = []
    for ciudad, g in df.sort_values("Date").groupby("City", observed=True):
        s = g.set_index("Date")[contaminante]
        partes.append(pd.DataFrame({
            "City": str(ciudad), "Date": s.index, "valor": s.values,
            "movil": s.rolling(ventana, min_periods=min_periodos).mean().values,
        }))
    return pd.concat(partes, ignore_index=True)


def banda_ciudades(movil, min_ciudades=3):
    """Percentiles 25/50/75 entre ciudades de la media móvil, por fecha."""
    m = movil.dropna(subset=["movil"])
    if m.empty:
        return pd.DataFrame(columns=["Date", "p25", "p50", "p75", "n"])
    b = (m.groupby("Date")["movil"]
          .agg(p25=lambda s: s.quantile(.25), p50="median", p75=lambda s: s.quantile(.75), n="size")
          .reset_index())
    return b[b["n"] >= min(min_ciudades, m["City"].nunique())].reset_index(drop=True)


def calendario(df, contaminante):
    """Mediana semanal por ciudad (semana que empieza el lunes), en formato largo."""
    if df.empty:
        return pd.DataFrame(columns=["City", "semana", "mediana", "n"])
    d = df[["City", "Date", contaminante]].copy()
    d["City"] = d["City"].astype(str)
    d["semana"] = d["Date"] - pd.to_timedelta(d["Date"].dt.dayofweek, unit="D")
    return (d.groupby(["City", "semana"])[contaminante]
             .agg(mediana="median", n="size").reset_index())


def por_mes(df, contaminante):
    """% de días sobre la guía y mediana por mes del año (solo meses con datos)."""
    if df.empty:
        return pd.DataFrame(columns=["mes", "nombre", "n", "pct_sobre_guia", "mediana"])
    g = guia(contaminante)
    r = (df.groupby("mes")[contaminante]
           .agg(n="size", pct_sobre_guia=lambda s: (s > g).mean() * 100, mediana="median")
           .reset_index())
    r["nombre"] = r["mes"].map(lambda m: MESES[m - 1])
    return r[["mes", "nombre", "n", "pct_sobre_guia", "mediana"]]


def episodios(df, contaminante, cuantil=0.95):
    """Días por encima del percentil `cuantil` de su propia ciudad, del mayor exceso al menor.

    El umbral es relativo a cada ciudad: un episodio es un día anómalo *para esa ciudad*.
    """
    cols = ["City", "Date", "valor", "umbral", "mediana_ciudad", "veces_mediana"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    d = df[["City", "Date", contaminante]].rename(columns={contaminante: "valor"}).copy()
    d["City"] = d["City"].astype(str)
    por_ciudad = d.groupby("City")["valor"]
    d["umbral"] = por_ciudad.transform(lambda s: s.quantile(cuantil))
    d["mediana_ciudad"] = por_ciudad.transform("median")
    d = d[d["valor"] > d["umbral"]].copy()
    d["veces_mediana"] = d["valor"] / d["mediana_ciudad"]
    return d.sort_values(["veces_mediana", "valor"], ascending=False).reset_index(drop=True)[cols]


def rachas(df, contaminante, umbral):
    """Racha más larga por ciudad de días *consecutivos* con el contaminante sobre `umbral`.

    Un hueco en el calendario (día sin medición) corta la racha: no se asume nada del día que falta.
    """
    cols = ["City", "dias", "desde", "hasta"]
    filas = []
    for ciudad, g in df.sort_values("Date").groupby("City", observed=True):
        mejor = (0, None, None)
        largo, inicio, previa = 0, None, None
        for fecha, sobre in zip(g["Date"], g[contaminante] > umbral):
            consecutivo = previa is not None and (fecha - previa).days == 1
            if sobre:
                if largo and consecutivo:
                    largo += 1
                else:
                    largo, inicio = 1, fecha
                if largo > mejor[0]:
                    mejor = (largo, inicio, fecha)
            else:
                largo = 0
            previa = fecha
        filas.append({"City": str(ciudad), "dias": mejor[0], "desde": mejor[1], "hasta": mejor[2]})
    if not filas:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(filas, columns=cols).sort_values("dias", ascending=False).reset_index(drop=True)


def integridad_sensor(df):
    """Lecturas físicamente imposibles (PM2.5 > PM10): total y por ciudad."""
    if df.empty:
        return np.nan, pd.DataFrame(columns=["City", "n", "pct_imposibles"])
    imposible = df["PM2.5"] > df["PM10"]
    por_ciudad = (imposible.groupby(df["City"].astype(str)).agg(n="size", pct_imposibles="mean")
                  .reset_index())
    por_ciudad["pct_imposibles"] *= 100
    return imposible.mean() * 100, por_ciudad.sort_values("pct_imposibles", ascending=False)

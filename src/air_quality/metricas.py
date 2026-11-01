"""Métricas del dashboard. Funciones puras sobre el dataset procesado (testeables sin UI)."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import CIUDADES
from .severidad import clasificar, guia, niveles


@dataclass(frozen=True)
class Filtros:
    desde: pd.Timestamp | None = None
    hasta: pd.Timestamp | None = None
    regiones: tuple = ()          # vacío = todas
    ciudades: tuple = ()          # vacío = todas
    contaminante: str = "PM2.5"
    niveles: tuple = ()           # vacío = todos (nombres de nivel del contaminante)


def filtrar(df, f: Filtros):
    m = pd.Series(True, index=df.index)
    if f.desde is not None:
        m &= df["Date"] >= pd.Timestamp(f.desde)
    if f.hasta is not None:
        m &= df["Date"] <= pd.Timestamp(f.hasta)
    if f.regiones:
        m &= df["region"].isin(f.regiones)
    if f.ciudades:
        m &= df["City"].isin(f.ciudades)
    if f.niveles:
        m &= clasificar(df[f.contaminante], f.contaminante).isin(f.niveles).values
    return df[m]


@dataclass(frozen=True)
class KPIs:
    n: int                   # días-ciudad
    n_ciudades: int
    pct_sobre_guia: float    # % de días-ciudad sobre la guía del contaminante
    mediana: float
    multiplo_guia: float     # mediana / guía
    pct_criticos: float      # % con las 3 guías (PM2.5, PM10, NO2) superadas a la vez
    pct_limpios: float       # % sin ninguna guía superada
    pct_sobre_it1: float     # % sobre la meta intermedia más laxa (nivel 5)


def kpis(df, contaminante="PM2.5"):
    if df.empty:
        return KPIs(0, 0, *([np.nan] * 6))
    s = df[contaminante]
    g = guia(contaminante)
    it1 = niveles(contaminante)[-1].desde
    return KPIs(
        n=len(df),
        n_ciudades=df["City"].nunique(),
        pct_sobre_guia=(s > g).mean() * 100,
        mediana=s.median(),
        multiplo_guia=s.median() / g,
        pct_criticos=(df["n_excedencias_oms"] == 3).mean() * 100,
        pct_limpios=(df["n_excedencias_oms"] == 0).mean() * 100,
        pct_sobre_it1=(s > it1).mean() * 100,
    )


def por_ciudad(df, contaminante="PM2.5"):
    """Una fila por ciudad con su nivel y coordenadas, de la más a la menos afectada."""
    columnas = ["City", "Country", "region", "lat", "lon", "n", "mediana",
                "pct_sobre_guia", "multiplo_guia", "pct_criticos"]
    if df.empty:
        return pd.DataFrame(columns=columnas)
    g = guia(contaminante)
    r = (df.groupby("City", observed=True)
           .agg(Country=("Country", "first"), region=("region", "first"), n=("Date", "size"),
                mediana=(contaminante, "median"),
                pct_sobre_guia=(contaminante, lambda s: (s > g).mean() * 100),
                pct_criticos=("n_excedencias_oms", lambda s: (s == 3).mean() * 100))
           .reset_index())
    r["City"] = r["City"].astype(str)
    r["multiplo_guia"] = r["mediana"] / g
    r["lat"] = r["City"].map(lambda c: CIUDADES[c][1])
    r["lon"] = r["City"].map(lambda c: CIUDADES[c][2])
    return (r.sort_values(["pct_sobre_guia", "mediana"], ascending=False)
             .reset_index(drop=True)[columnas])


def distribucion_niveles(df, contaminante="PM2.5"):
    """% de días de cada ciudad en cada nivel OMS (formato largo, todas las combinaciones)."""
    nv = niveles(contaminante)
    if df.empty:
        return pd.DataFrame(columns=["City", "nivel", "indice", "n", "pct"])
    d = df[["City"]].assign(nivel=clasificar(df[contaminante], contaminante).values)
    d["City"] = d["City"].astype(str)
    conteo = d.groupby(["City", "nivel"], observed=False).size().rename("n").reset_index()
    conteo["pct"] = conteo["n"] / conteo.groupby("City")["n"].transform("sum") * 100
    conteo["indice"] = conteo["nivel"].map({n.nombre: n.indice for n in nv}).astype(int)
    return conteo[["City", "nivel", "indice", "n", "pct"]]


def nombre_ciudad(c):
    """'mexico city' → 'Mexico City' para mostrar."""
    return str(c).title()

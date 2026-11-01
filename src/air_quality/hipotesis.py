"""Métricas del capítulo 03: análisis de causa raíz por eliminación de hipótesis.

Cada factor candidato se evalúa con dos preguntas independientes:

1. ¿La diferencia es real? Prueba no paramétrica (los datos no son normales, Fase II):
   Spearman para factores continuos, Kruskal-Wallis para categorías, Mann-Whitney para binarios.
2. ¿Importa? Tamaño del efecto = diferencia entre la mediana del grupo más y menos contaminado
   (los continuos se agrupan en cuartiles). Es relevante si supera `relevancia` × mediana global.

Solo una hipótesis que pasa ambas se considera confirmada.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

ALFA = 0.05
RELEVANCIA = 0.10   # 10 % de la mediana global
MIN_POR_GRUPO = 10


@dataclass(frozen=True)
class Factor:
    nombre: str
    columna: str
    tipo: str          # "continuo" | "categoria" | "binario"
    unidad: str = ""


FACTORES = [
    Factor("Viento", "Wind Speed", "continuo", "m/s"),
    Factor("Temperatura", "Temperature", "continuo", "°C"),
    Factor("Humedad", "Humidity", "continuo", "%"),
    Factor("Estación", "trimestre_met", "categoria"),
    Factor("Fin de semana", "fin_semana", "binario"),
    Factor("Ciudad", "City", "categoria"),
]
POR_NOMBRE = {f.nombre: f for f in FACTORES}
ORDEN_ESTACION = ["DEF", "MAM", "JJA", "SON"]
NOMBRE_ESTACION = {"DEF": "Dic–Feb", "MAM": "Mar–May", "JJA": "Jun–Ago", "SON": "Sep–Nov"}


def _etiquetas_cuartil(serie, unidad):
    _, bordes = pd.qcut(serie, 4, retbins=True)
    return [f"Q{i + 1} · {bordes[i]:.0f}–{bordes[i + 1]:.0f} {unidad}".strip() for i in range(4)]


def _grupo(df, factor: Factor):
    s = df[factor.columna]
    if factor.tipo == "continuo":
        etiquetas = _etiquetas_cuartil(s, factor.unidad)
        return pd.qcut(s, 4, labels=etiquetas)
    if factor.tipo == "binario":
        return s.map({True: "Fin de semana", False: "Laborable"})
    if factor.columna == "trimestre_met":
        return pd.Categorical(s.astype(str).map(NOMBRE_ESTACION),
                              categories=[NOMBRE_ESTACION[e] for e in ORDEN_ESTACION], ordered=True)
    return s.astype(str)


def grupos(df, contaminante, factor):
    """Mediana e IQR del contaminante en cada grupo del factor."""
    factor = POR_NOMBRE[factor] if isinstance(factor, str) else factor
    cols = ["grupo", "n", "mediana", "p25", "p75"]
    if df.empty or df[factor.columna].nunique() < 2:
        return pd.DataFrame(columns=cols)
    g = pd.Series(_grupo(df, factor), index=df.index, name="grupo")
    r = (df[contaminante].groupby(g, observed=True)
           .agg(n="size", mediana="median", p25=lambda s: s.quantile(.25),
                p75=lambda s: s.quantile(.75))
           .reset_index())
    r["grupo"] = r["grupo"].astype(str)
    if factor.tipo in ("categoria",) and factor.columna == "City":
        r = r.sort_values("mediana").reset_index(drop=True)
    return r[cols]


def _prueba(df, contaminante, factor: Factor):
    y = df[contaminante]
    if factor.tipo == "continuo":
        rho, p = stats.spearmanr(df[factor.columna], y)
        return "Spearman", f"ρ = {rho:+.3f}", rho, p
    muestras = [y[df[factor.columna] == v] for v in df[factor.columna].dropna().unique()]
    muestras = [m for m in muestras if len(m) >= MIN_POR_GRUPO]
    if factor.tipo == "binario":
        u, p = stats.mannwhitneyu(*muestras)
        return "Mann-Whitney U", f"U = {u:,.0f}", u, p
    h, p = stats.kruskal(*muestras)
    return "Kruskal-Wallis", f"H = {h:.2f}", h, p


def veredicto(p, efecto, umbral):
    if np.isnan(p):
        return "No aplica"
    if p < ALFA and efecto >= umbral:
        return "Confirmada"
    if p < ALFA:
        return "Real pero menor"
    return "Descartada"


def evaluar(df, contaminante, relevancia=RELEVANCIA):
    """Una fila por factor: prueba, p-valor, tamaño del efecto y veredicto."""
    cols = ["factor", "prueba", "estadistico", "p", "efecto", "efecto_rel", "umbral",
            "grupo_min", "grupo_max", "n_grupos", "veredicto"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    umbral = relevancia * df[contaminante].median()
    filas = []
    for f in FACTORES:
        g = grupos(df, contaminante, f)
        g = g[g["n"] >= MIN_POR_GRUPO]
        if len(g) < 2:
            filas.append(dict(factor=f.nombre, prueba="—", estadistico="", p=np.nan, efecto=np.nan,
                              efecto_rel=np.nan, umbral=umbral, grupo_min="", grupo_max="",
                              n_grupos=len(g), veredicto="No aplica"))
            continue
        prueba, texto, _, p = _prueba(df, contaminante, f)
        efecto = g["mediana"].max() - g["mediana"].min()
        filas.append(dict(
            factor=f.nombre, prueba=prueba, estadistico=texto, p=p, efecto=efecto,
            efecto_rel=efecto / df[contaminante].median() * 100, umbral=umbral,
            grupo_min=g.loc[g["mediana"].idxmin(), "grupo"],
            grupo_max=g.loc[g["mediana"].idxmax(), "grupo"],
            n_grupos=len(g), veredicto=veredicto(p, efecto, umbral)))
    return pd.DataFrame(filas, columns=cols)


def finde_por_ciudad(df, contaminante):
    """Mediana en días laborables y de fin de semana por ciudad (para el dumbbell)."""
    cols = ["City", "laborable", "fin_semana", "diferencia", "p"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    t = (df.assign(City=df["City"].astype(str))
           .pivot_table(index="City", columns="fin_semana", values=contaminante, aggfunc="median",
                        observed=True))
    t = t.rename(columns={False: "laborable", True: "fin_semana"}).dropna().reset_index()
    if t.empty or "laborable" not in t or "fin_semana" not in t:
        return pd.DataFrame(columns=cols)
    t["diferencia"] = t["fin_semana"] - t["laborable"]
    ciudad = df["City"].astype(str)
    t["p"] = [stats.mannwhitneyu(df.loc[(ciudad == c) & df["fin_semana"], contaminante],
                                 df.loc[(ciudad == c) & ~df["fin_semana"], contaminante]).pvalue
              if ((ciudad == c) & df["fin_semana"]).sum() >= MIN_POR_GRUPO
              and ((ciudad == c) & ~df["fin_semana"]).sum() >= MIN_POR_GRUPO else np.nan
              for c in t["City"]]
    return t.sort_values("diferencia").reset_index(drop=True)[cols]

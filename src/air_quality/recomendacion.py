"""Métricas del capítulo 04: simulador de reducción, hoja de ruta por metas OMS y prioridad de ciudades.

El simulador usa un modelo de *rollback* proporcional: recortar un X % las emisiones de fondo baja
en la misma proporción cada concentración diaria. Es la aproximación más simple que se usa en
gestión de calidad del aire, y es coherente con el capítulo 03: si ni el clima ni el calendario
modulan la contaminación, el nivel observado es casi todo fondo.
"""

import numpy as np
import pandas as pd

from .severidad import METAS_OMS, clasificar, niveles

# La guía de 24 h de la OMS 2021 se define como el percentil 99 anual (3-4 días de excedencia al año).
COBERTURA_OMS = 0.99


def simular(df, contaminante, reduccion):
    """% de días en cada nivel OMS hoy y con las concentraciones recortadas un `reduccion` %."""
    cols = ["nivel", "indice", "pct_actual", "pct_simulado"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    if not 0 <= reduccion <= 100:
        raise ValueError(f"La reducción debe estar entre 0 y 100 %, no {reduccion}")
    s = df[contaminante]
    nv = niveles(contaminante)
    actual = clasificar(s, contaminante).value_counts(normalize=True, sort=False)
    simulado = clasificar(s * (1 - reduccion / 100), contaminante).value_counts(normalize=True, sort=False)
    return pd.DataFrame({
        "nivel": [n.nombre for n in nv],
        "indice": [n.indice for n in nv],
        "pct_actual": [actual.get(n.nombre, 0) * 100 for n in nv],
        "pct_simulado": [simulado.get(n.nombre, 0) * 100 for n in nv],
    })[cols]


def reduccion_necesaria(df, contaminante, cobertura=COBERTURA_OMS):
    """Recorte (%) que deja el `cobertura` de los días en o bajo cada meta OMS, de la más laxa a la guía.

    Con rollback proporcional basta con llevar el percentil `cobertura` hasta la meta:
    reducción = 1 − meta / percentil. Si el percentil ya está bajo la meta, la reducción es 0.
    """
    cols = ["meta", "valor", "reduccion"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    p = df[contaminante].quantile(cobertura)
    metas = list(METAS_OMS[contaminante].items())[::-1]          # IT-1 primero, guía al final
    filas = [{"meta": m, "valor": v, "reduccion": max(0.0, (1 - v / p) * 100) if p > 0 else 0.0}
             for m, v in metas]
    return pd.DataFrame(filas, columns=cols)


def prioridad_ciudades(df, contaminante):
    """Una fila por ciudad con los indicadores para priorizar, de la más a la menos crítica.

    `pct_criticos`: días con las tres guías (PM2.5, PM10 y NO2) superadas a la vez.
    """
    cols = ["City", "region", "n", "dias_criticos", "pct_criticos", "pct_sobre_it1", "mediana",
            "reduccion_guia", "pct_imposibles"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    it1 = niveles(contaminante)[-1].desde
    guia = METAS_OMS[contaminante]["guía"]
    filas = []
    for ciudad, g in df.groupby("City", observed=True):
        s = g[contaminante]
        p = s.quantile(COBERTURA_OMS)
        criticos = int((g["n_excedencias_oms"] == 3).sum())
        filas.append({
            "City": str(ciudad), "region": g["region"].iloc[0], "n": len(g),
            "dias_criticos": criticos, "pct_criticos": criticos / len(g) * 100,
            "pct_sobre_it1": (s > it1).mean() * 100, "mediana": s.median(),
            "reduccion_guia": max(0.0, (1 - guia / p) * 100) if p > 0 else 0.0,
            "pct_imposibles": (g["PM2.5"] > g["PM10"]).mean() * 100,
        })
    return (pd.DataFrame(filas, columns=cols)
              .sort_values(["pct_criticos", "pct_sobre_it1"], ascending=False)
              .reset_index(drop=True))


def resumen_escenario(sim):
    """Cifras del escenario: % que cumple la guía y % sobre IT-1, antes y después."""
    if sim.empty:
        return dict(guia_antes=np.nan, guia_despues=np.nan, it1_antes=np.nan, it1_despues=np.nan)
    return dict(guia_antes=float(sim["pct_actual"].iloc[0]), guia_despues=float(sim["pct_simulado"].iloc[0]),
                it1_antes=float(sim["pct_actual"].iloc[-1]), it1_despues=float(sim["pct_simulado"].iloc[-1]))

"""Escala de severidad basada en las guías y metas intermedias (IT) de la OMS 2021 para 24 h.

Cada nivel se identifica con un `indice` global de 0 a 5 que es el mismo para todos los
contaminantes (0 = cumple la guía, 5 = supera IT-1), así un mismo color significa lo mismo
aunque el contaminante no tenga todas las metas intermedias (el NO2 solo tiene IT-1 e IT-2).
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

# µg/m³, en orden creciente de concentración: guía < IT-4 < IT-3 < IT-2 < IT-1
METAS_OMS = {
    "PM2.5": {"guía": 15, "IT-4": 25, "IT-3": 37.5, "IT-2": 50, "IT-1": 75},
    "PM10":  {"guía": 45, "IT-4": 50, "IT-3": 75, "IT-2": 100, "IT-1": 150},
    "NO2":   {"guía": 25, "IT-2": 50, "IT-1": 120},
}

# índice global del nivel que empieza al superar cada meta
_INDICE_AL_SUPERAR = {"guía": 1, "IT-4": 2, "IT-3": 3, "IT-2": 4, "IT-1": 5}
N_NIVELES = 6


@dataclass(frozen=True)
class Nivel:
    indice: int          # 0..5, compartido entre contaminantes (define el color)
    nombre: str          # "Cumple guía", "Sobre IT-3", ...
    desde: float         # límite inferior exclusivo (-inf para el primero)
    hasta: float         # límite superior inclusivo (inf para el último)

    @property
    def rango(self):
        if np.isinf(self.desde):
            return f"≤ {self.hasta:g}"
        if np.isinf(self.hasta):
            return f"> {self.desde:g}"
        return f"{self.desde:g}–{self.hasta:g}"


def niveles(contaminante):
    """Niveles de severidad del contaminante, del más limpio al más severo."""
    if contaminante not in METAS_OMS:
        raise KeyError(f"Sin metas OMS para {contaminante!r}; opciones: {list(METAS_OMS)}")
    metas = list(METAS_OMS[contaminante].items())
    resultado = [Nivel(0, "Cumple guía", -np.inf, metas[0][1])]
    for i, (meta, valor) in enumerate(metas):
        hasta = metas[i + 1][1] if i + 1 < len(metas) else np.inf
        nombre = "Sobre guía" if meta == "guía" else f"Sobre {meta}"
        resultado.append(Nivel(_INDICE_AL_SUPERAR[meta], nombre, valor, hasta))
    return resultado


def nombres_niveles(contaminante):
    return [n.nombre for n in niveles(contaminante)]


def clasificar(valores, contaminante):
    """Nivel de cada valor como categoría ordenada (NaN si el valor es NaN)."""
    nv = niveles(contaminante)
    bordes = [-np.inf] + [n.hasta for n in nv]
    return pd.cut(pd.Series(valores), bins=bordes, labels=[n.nombre for n in nv],
                  right=True, ordered=True)


def guia(contaminante):
    return METAS_OMS[contaminante]["guía"]

import numpy as np
import pandas as pd
import pytest

from air_quality.config import METEO, POLL


@pytest.fixture
def crudo_sintetico():
    """Dataset con la forma del CSV crudo: 3 ciudades x 40 días, con los defectos reales.

    - Ciudades con mayúsculas y espacios inconsistentes.
    - Fechas en formato M/D/YYYY.
    - Nulos sueltos en los contaminantes.
    - Duplicados exactos y un duplicado de clave con menos columnas informadas.
    """
    rng = np.random.default_rng(0)
    ciudades = {"Lima": "Peru", "São Paulo": "Brazil", "Paris": "France"}
    variantes = {"Lima": [" lima", "LIMA", "Lima "], "São Paulo": ["sao paulo", "São  Paulo"],
                 "Paris": ["Paris", "paris"]}
    fechas = pd.date_range("2023-01-01", periods=40, freq="D")
    filas = []
    for ciudad, pais in ciudades.items():
        for i, f in enumerate(fechas):
            fila = {"City": variantes[ciudad][i % len(variantes[ciudad])], "Country": pais,
                    "Date": f"{f.month}/{f.day}/{f.year}"}
            fila.update({c: round(float(rng.uniform(5, 150)), 2) for c in POLL})
            fila.update({"Temperature": round(float(rng.uniform(-10, 40)), 2),
                         "Humidity": round(float(rng.uniform(10, 100)), 2),
                         "Wind Speed": round(float(rng.uniform(0.5, 20)), 2)})
            filas.append(fila)
    df = pd.DataFrame(filas, columns=["City", "Country", "Date"] + POLL + METEO)

    for c, idx in zip(POLL, [3, 50, 77, 90, 101, 15]):
        df.loc[idx, c] = np.nan

    exactos = df.iloc[[0, 1, 2]]
    parcial = df.iloc[[10]].copy()
    parcial["PM2.5"] = np.nan          # misma clave, registro menos completo
    return pd.concat([df, exactos, parcial], ignore_index=True)

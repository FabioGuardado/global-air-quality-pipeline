import numpy as np
import pandas as pd
import pytest

from air_quality.hipotesis import (FACTORES, evaluar, finde_por_ciudad, grupos, veredicto)


def _df(n=800, efecto_viento=0.0, seed=0):
    """Dataset sintético con 4 ciudades; `efecto_viento` µg/m³ menos por cada m/s de viento."""
    rng = np.random.default_rng(seed)
    viento = rng.uniform(0.5, 20, n)
    fechas = pd.Timestamp("2023-01-01") + pd.to_timedelta(rng.integers(0, 365, n), unit="D")
    return pd.DataFrame({
        "City": rng.choice(["paris", "madrid", "tokyo", "seoul"], n),
        "Date": fechas,
        "PM2.5": rng.uniform(40, 120, n) - efecto_viento * viento,
        "Wind Speed": viento,
        "Temperature": rng.uniform(-10, 40, n),
        "Humidity": rng.uniform(10, 100, n),
        "trimestre_met": pd.Series(fechas.month).map(
            {12: "DEF", 1: "DEF", 2: "DEF", 3: "MAM", 4: "MAM", 5: "MAM", 6: "JJA", 7: "JJA",
             8: "JJA", 9: "SON", 10: "SON", 11: "SON"}).values,
        "fin_semana": fechas.dayofweek >= 5,
    })


@pytest.mark.parametrize("p, efecto, esperado", [
    (0.001, 20, "Confirmada"), (0.001, 1, "Real pero menor"), (0.4, 20, "Descartada"),
    (np.nan, 0, "No aplica"),
])
def test_veredicto(p, efecto, esperado):
    assert veredicto(p, efecto, umbral=7.8) == esperado


def test_sin_relacion_todo_descartado():
    ev = evaluar(_df(), "PM2.5")
    assert list(ev["factor"]) == [f.nombre for f in FACTORES]
    assert set(ev["veredicto"]) <= {"Descartada", "Real pero menor"}


def test_detecta_un_efecto_real_y_relevante():
    ev = evaluar(_df(efecto_viento=3.0), "PM2.5").set_index("factor")
    assert ev.loc["Viento", "veredicto"] == "Confirmada"
    assert ev.loc["Viento", "efecto"] > ev.loc["Viento", "umbral"]
    assert ev.loc["Viento", "grupo_min"].startswith("Q4")       # más viento, menos PM2.5


def test_una_sola_ciudad_no_aplica():
    df = _df()
    ev = evaluar(df[df["City"] == "paris"], "PM2.5").set_index("factor")
    assert ev.loc["Ciudad", "veredicto"] == "No aplica"
    assert np.isnan(ev.loc["Ciudad", "p"])


def test_grupos_cuartiles_etiquetados_y_ordenados():
    g = grupos(_df(), "PM2.5", "Viento")
    assert len(g) == 4
    assert [x[:2] for x in g["grupo"]] == ["Q1", "Q2", "Q3", "Q4"]
    assert g["grupo"].str.endswith("m/s").all()
    assert (g["p25"] <= g["mediana"]).all() and (g["mediana"] <= g["p75"]).all()


def test_grupos_estacion_en_orden_cronologico():
    g = grupos(_df(), "PM2.5", "Estación")
    assert g["grupo"].tolist() == ["Dic–Feb", "Mar–May", "Jun–Ago", "Sep–Nov"]


def test_finde_por_ciudad():
    d = finde_por_ciudad(_df(), "PM2.5")
    assert set(d["City"]) == {"paris", "madrid", "tokyo", "seoul"}
    assert np.allclose(d["diferencia"], d["fin_semana"] - d["laborable"])
    assert d["diferencia"].is_monotonic_increasing
    assert d["p"].between(0, 1).all()


def test_vacio():
    vacio = _df().iloc[0:0]
    assert evaluar(vacio, "PM2.5").empty
    assert finde_por_ciudad(vacio, "PM2.5").empty

import numpy as np
import pandas as pd
import pytest

from air_quality.recomendacion import (prioridad_ciudades, reduccion_necesaria, resumen_escenario,
                                       simular)


def _df(ciudad, pm25, pm10=None, exc=None):
    n = len(pm25)
    return pd.DataFrame({"City": ciudad, "region": "Europa", "Date": pd.date_range("2023-01-01", periods=n),
                         "PM2.5": pm25, "PM10": pm10 if pm10 is not None else [200.0] * n,
                         "n_excedencias_oms": exc if exc is not None else [0] * n})


def test_simular_sin_reduccion_reproduce_la_distribucion_actual():
    sim = simular(_df("paris", [10.0, 20, 80, 100]), "PM2.5", 0)
    assert np.allclose(sim["pct_actual"], sim["pct_simulado"])
    assert sim["pct_actual"].sum() == pytest.approx(100)
    assert sim.loc[sim["nivel"] == "Sobre IT-1", "pct_actual"].item() == pytest.approx(50)


def test_simular_recorta_proporcionalmente():
    # 100 → 50 con −50 %: pasa de "Sobre IT-1" (> 75) a "Sobre IT-3" (37.5–50]
    sim = simular(_df("paris", [100.0]), "PM2.5", 50).set_index("nivel")
    assert sim.loc["Sobre IT-1", "pct_actual"] == 100
    assert sim.loc["Sobre IT-3", "pct_simulado"] == 100


def test_simular_valida_el_rango():
    with pytest.raises(ValueError):
        simular(_df("paris", [10.0]), "PM2.5", 120)


def test_reduccion_necesaria_lleva_el_percentil_a_cada_meta():
    req = reduccion_necesaria(_df("paris", [150.0] * 10), "PM2.5", cobertura=0.99).set_index("meta")
    assert list(req.index) == ["IT-1", "IT-2", "IT-3", "IT-4", "guía"]     # de la más laxa a la guía
    assert req.loc["IT-1", "reduccion"] == pytest.approx(50)               # 150 → 75
    assert req.loc["guía", "reduccion"] == pytest.approx(90)               # 150 → 15
    assert req["reduccion"].is_monotonic_increasing


def test_reduccion_necesaria_es_cero_si_ya_se_cumple():
    req = reduccion_necesaria(_df("paris", [5.0, 8, 10]), "PM2.5")
    assert (req["reduccion"] == 0).all()


def test_no2_solo_tiene_dos_metas_intermedias():
    req = reduccion_necesaria(_df("paris", [100.0]).assign(NO2=100.0), "NO2")
    assert req["meta"].tolist() == ["IT-1", "IT-2", "guía"]


def test_prioridad_ordena_por_dias_criticos():
    a = _df("paris", [80.0] * 4, exc=[3, 3, 0, 0])
    b = _df("madrid", [80.0] * 4, exc=[3, 3, 3, 0], pm10=[50.0, 200, 200, 200])
    p = prioridad_ciudades(pd.concat([a, b]), "PM2.5")
    assert p["City"].tolist() == ["madrid", "paris"]
    assert p.loc[0, "dias_criticos"] == 3
    assert p.loc[0, "pct_criticos"] == pytest.approx(75)
    assert p.loc[0, "pct_imposibles"] == pytest.approx(25)        # 80 > 50 en un día
    assert p.loc[0, "reduccion_guia"] == pytest.approx((1 - 15 / 80) * 100)


def test_vacios():
    vacio = _df("paris", []).iloc[0:0]
    assert simular(vacio, "PM2.5", 10).empty
    assert reduccion_necesaria(vacio, "PM2.5").empty
    assert prioridad_ciudades(vacio, "PM2.5").empty
    assert np.isnan(resumen_escenario(simular(vacio, "PM2.5", 10))["guia_antes"])

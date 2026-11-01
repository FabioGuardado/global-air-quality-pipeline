import numpy as np
import pandas as pd
import pytest

from air_quality.config import CIUDADES, REGIONES
from air_quality.derivadas import agregar_derivadas, agregar_ordinales, agregar_region
from air_quality.limpieza import agregar_variables_tiempo


def _base():
    df = pd.DataFrame({
        "City": ["paris", "paris", "madrid", "madrid", "madrid"],
        "Date": pd.to_datetime(["2023-01-01", "2023-01-02",
                                "2023-01-01", "2023-01-02", "2023-01-20"]),
        "PM2.5": [10.0, 20.0, 30.0, 50.0, 10.0],
        "PM10": [20.0, 40.0, 20.0, 100.0, 50.0],
        "NO2": [10.0, 30.0, 30.0, 10.0, 26.0],
    })
    return agregar_variables_tiempo(df)


def test_ordena_por_ciudad_y_fecha():
    out = agregar_derivadas(_base())
    assert out["City"].tolist() == ["madrid", "madrid", "madrid", "paris", "paris"]


def test_ratio_y_marca_imposible():
    out = agregar_derivadas(_base()).set_index(["City", "Date"])
    assert out.loc[("madrid", "2023-01-01"), "ratio_pm"] == pytest.approx(1.5)
    assert out.loc[("madrid", "2023-01-01"), "ratio_pm_imposible"]
    assert not out.loc[("paris", "2023-01-01"), "ratio_pm_imposible"]


def test_excedencias_oms():
    out = agregar_derivadas(_base())
    # madrid/01-01: PM2.5 30>15, PM10 20<=45, NO2 30>25 → 2 ... paris/01-01: nada supera → 0
    assert out["n_excedencias_oms"].tolist() == [2, 2, 2, 0, 2]
    assert out["n_excedencias_oms"].between(0, 3).all()


def test_pm25_vs_ciudad_centra_en_la_mediana():
    out = agregar_derivadas(_base())
    assert out.groupby("City")["pm25_vs_ciudad"].median().abs().max() == 0


def test_media_movil_usa_dias_reales_y_no_cruza_ciudades():
    out = agregar_derivadas(_base())
    a = out[out["City"] == "madrid"]["pm25_movil_7d"].tolist()
    # el 20 de enero está fuera de la ventana de 7 días: no promedia con los anteriores
    assert a == [30.0, 40.0, 10.0]
    assert out[out["City"] == "paris"]["pm25_movil_7d"].tolist() == [10.0, 15.0]


def test_delta_reinicia_en_cada_ciudad():
    out = agregar_derivadas(_base())
    assert out["pm25_delta"].tolist() == [0.0, 20.0, -40.0, 0.0, 10.0]


def test_variables_temporales():
    out = agregar_derivadas(_base())
    assert set(out["trimestre_met"]) == {"DEF"}
    assert np.allclose(out["mes_sin"] ** 2 + out["mes_cos"] ** 2, 1)
    assert np.allclose(out["dia_sem_sin"] ** 2 + out["dia_sem_cos"] ** 2, 1)


def test_region_desde_ciudad():
    df = agregar_variables_tiempo(pd.DataFrame({
        "City": ["madrid", "sydney"], "Date": pd.to_datetime(["2023-01-01", "2023-01-01"]),
        "PM2.5": [1.0, 2.0], "PM10": [2.0, 4.0], "NO2": [1.0, 1.0]}))
    out = agregar_derivadas(df)
    assert out["region"].astype(str).tolist() == ["Europa", "Oceanía"]
    assert out["region"].cat.ordered


def test_ciudad_sin_region_falla_explicitamente():
    df = pd.DataFrame({"City": ["atlantis"]})
    with pytest.raises(ValueError, match="atlantis"):
        agregar_region(df)


def test_todas_las_ciudades_configuradas_tienen_region_valida():
    assert {r for r, _, _ in CIUDADES.values()} <= set(REGIONES)


def test_ordinales():
    df = pd.DataFrame({"viento_cat": pd.Categorical(["alto", "muy bajo", "medio"]),
                       "fin_semana": [True, False, True]})
    out = agregar_ordinales(df)
    assert out["viento_ord"].tolist() == [3, 0, 2]
    assert out["fin_semana_int"].tolist() == [1, 0, 1]

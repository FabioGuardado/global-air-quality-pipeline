import numpy as np
import pandas as pd
import pytest

from air_quality.metricas import (Filtros, distribucion_niveles, filtrar, kpis, nombre_ciudad,
                                  por_ciudad)


@pytest.fixture
def df():
    """4 días en Sydney (Oceanía) y 2 en Paris (Europa)."""
    return pd.DataFrame({
        "City": ["sydney"] * 4 + ["paris"] * 2,
        "Country": ["australia"] * 4 + ["france"] * 2,
        "region": pd.Categorical(["Oceanía"] * 4 + ["Europa"] * 2),
        "Date": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-02-01", "2023-03-01",
                                "2023-01-01", "2023-02-01"]),
        "PM2.5": [10.0, 20.0, 80.0, 40.0, 14.0, 100.0],
        "n_excedencias_oms": [0, 1, 3, 2, 0, 3],
    })


def test_filtrar_sin_filtros_devuelve_todo(df):
    assert len(filtrar(df, Filtros())) == 6


def test_filtrar_por_fecha_region_y_ciudad(df):
    assert len(filtrar(df, Filtros(desde="2023-01-15", hasta="2023-02-28"))) == 2
    assert set(filtrar(df, Filtros(regiones=("Europa",)))["City"]) == {"paris"}
    assert len(filtrar(df, Filtros(ciudades=("sydney",)))) == 4


def test_filtrar_por_nivel_usa_el_contaminante(df):
    r = filtrar(df, Filtros(niveles=("Cumple guía",)))
    assert r["PM2.5"].tolist() == [10.0, 14.0]


def test_filtros_combinados_pueden_quedar_vacios(df):
    assert filtrar(df, Filtros(regiones=("Europa",), ciudades=("sydney",))).empty


def test_kpis(df):
    k = kpis(df)
    assert k.n == 6 and k.n_ciudades == 2
    assert k.pct_sobre_guia == pytest.approx(4 / 6 * 100)
    assert k.mediana == 30.0
    assert k.multiplo_guia == pytest.approx(2.0)
    assert k.pct_criticos == pytest.approx(2 / 6 * 100)
    assert k.pct_limpios == pytest.approx(2 / 6 * 100)
    assert k.pct_sobre_it1 == pytest.approx(2 / 6 * 100)


def test_kpis_vacio_no_falla(df):
    k = kpis(df.iloc[0:0])
    assert k.n == 0 and np.isnan(k.pct_sobre_guia)


def test_por_ciudad_ordenado_y_con_coordenadas(df):
    r = por_ciudad(df)
    assert r["City"].tolist() == ["sydney", "paris"]          # 75 % vs 50 % sobre la guía
    assert r.loc[0, "pct_sobre_guia"] == pytest.approx(75)
    assert r.loc[1, "mediana"] == 57.0
    assert r.loc[0, "lat"] < 0 < r.loc[1, "lat"]


def test_por_ciudad_vacio(df):
    assert por_ciudad(df.iloc[0:0]).empty


def test_distribucion_niveles_suma_100_y_completa(df):
    d = distribucion_niveles(df)
    assert d.groupby("City")["pct"].sum().round(6).eq(100).all()
    assert len(d) == 2 * 6                       # todas las combinaciones ciudad x nivel
    sydney = d[d["City"] == "sydney"].set_index("nivel")
    assert sydney.loc["Sobre IT-1", "n"] == 1 and sydney.loc["Sobre IT-4", "n"] == 0


def test_nombre_ciudad():
    assert nombre_ciudad("mexico city") == "Mexico City"

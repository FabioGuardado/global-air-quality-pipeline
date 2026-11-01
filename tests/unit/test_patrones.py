import numpy as np
import pandas as pd
import pytest

from air_quality.patrones import (banda_ciudades, calendario, episodios, integridad_sensor,
                                  por_mes, rachas, serie_movil)


def _df(ciudad, fechas, valores, pm10=None):
    fechas = pd.to_datetime(fechas)
    return pd.DataFrame({"City": ciudad, "Date": fechas, "PM2.5": valores,
                         "PM10": pm10 if pm10 is not None else [200.0] * len(valores),
                         "mes": fechas.month})


def test_racha_cuenta_solo_dias_consecutivos():
    # 3 días seguidos sobre 75, hueco de un día, 4 días seguidos sobre 75
    fechas = ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-05", "2023-01-06",
              "2023-01-07", "2023-01-08"]
    r = rachas(_df("paris", fechas, [80.0] * 7), "PM2.5", 75)
    assert r.loc[0, "dias"] == 4
    assert r.loc[0, "desde"] == pd.Timestamp("2023-01-05")
    assert r.loc[0, "hasta"] == pd.Timestamp("2023-01-08")


def test_racha_se_corta_bajo_el_umbral_y_ordena_por_ciudad():
    a = _df("paris", pd.date_range("2023-01-01", periods=5), [80, 80, 10, 80, 80.0])
    b = _df("madrid", pd.date_range("2023-01-01", periods=3), [90, 90, 90.0])
    r = rachas(pd.concat([a, b]), "PM2.5", 75)
    assert r["City"].tolist() == ["madrid", "paris"]
    assert r["dias"].tolist() == [3, 2]


def test_racha_sin_dias_sobre_umbral():
    r = rachas(_df("paris", pd.date_range("2023-01-01", periods=3), [1, 2, 3.0]), "PM2.5", 75)
    assert r.loc[0, "dias"] == 0


def test_episodios_relativos_a_cada_ciudad():
    rng = np.random.default_rng(0)
    alta = _df("paris", pd.date_range("2023-01-01", periods=100), rng.uniform(100, 110, 100))
    baja = _df("madrid", pd.date_range("2023-01-01", periods=100), rng.uniform(10, 20, 100))
    ep = episodios(pd.concat([alta, baja]), "PM2.5", cuantil=0.95)
    # cada ciudad aporta su 5 % superior, aunque los valores de Madrid sean bajos en absoluto
    assert ep.groupby("City").size().to_dict() == {"madrid": 5, "paris": 5}
    assert (ep["valor"] > ep["umbral"]).all()
    assert ep["veces_mediana"].is_monotonic_decreasing


def test_serie_movil_ventana_de_dias_reales():
    d = _df("paris", ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-20"], [10, 20, 30, 100.0])
    m = serie_movil(d, "PM2.5")
    assert np.isnan(m.loc[1, "movil"])                 # menos de 3 días en la ventana
    assert m.loc[2, "movil"] == 20.0
    assert np.isnan(m.loc[3, "movil"])                 # el 20 de enero queda solo


def test_banda_percentiles_entre_ciudades():
    fechas = pd.date_range("2023-01-01", periods=5)
    d = pd.concat([_df(c, fechas, [v] * 5) for c, v in [("a", 10.0), ("b", 20.0), ("c", 30.0)]])
    b = banda_ciudades(serie_movil(d, "PM2.5"))
    assert (b["p50"] == 20).all() and (b["p25"] == 15).all() and (b["p75"] == 25).all()


def test_calendario_semana_empieza_el_lunes():
    d = _df("paris", ["2023-01-02", "2023-01-08", "2023-01-09"], [10, 30, 50.0])   # lun, dom, lun
    c = calendario(d, "PM2.5")
    assert c["semana"].tolist() == [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-09")]
    assert c["mediana"].tolist() == [20.0, 50.0]
    assert c["n"].tolist() == [2, 1]


def test_por_mes():
    d = _df("paris", ["2023-01-01", "2023-01-02", "2023-02-01"], [10, 20, 30.0])
    m = por_mes(d, "PM2.5")
    assert m["nombre"].tolist() == ["Ene", "Feb"]
    assert m["pct_sobre_guia"].tolist() == [50.0, 100.0]


def test_integridad_sensor():
    d = pd.concat([_df("paris", pd.date_range("2023-01-01", periods=4), [10, 10, 50, 50.0],
                       pm10=[20, 20, 20, 20.0]),
                   _df("madrid", pd.date_range("2023-01-01", periods=2), [10, 10.0], pm10=[20, 20.0])])
    total, por_ciudad = integridad_sensor(d)
    assert total == pytest.approx(2 / 6 * 100)
    assert por_ciudad.set_index("City")["pct_imposibles"].to_dict() == {"paris": 50.0, "madrid": 0.0}


@pytest.mark.parametrize("fn", [serie_movil, calendario, por_mes, episodios])
def test_vacios_no_fallan(fn):
    vacio = _df("paris", [], [])
    assert fn(vacio, "PM2.5").empty


def test_integridad_vacia():
    total, por_ciudad = integridad_sensor(_df("paris", [], []))
    assert np.isnan(total) and por_ciudad.empty

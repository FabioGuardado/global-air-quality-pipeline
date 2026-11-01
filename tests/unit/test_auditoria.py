import numpy as np
import pandas as pd

from air_quality.auditoria import comparar_distribuciones, delta_spearman, verificar


def _procesado(pm25, pm10, ciudades=None):
    n = len(pm25)
    return pd.DataFrame({"City": ciudades or ["paris"] * n, "Country": "france",
                         "Date": pd.date_range("2023-01-01", periods=n), "PM2.5": pm25, "PM10": pm10})


def test_distribucion_identica_queda_intacta():
    rng = np.random.default_rng(0)
    x = pd.DataFrame({"a": rng.normal(50, 10, 500)})
    d = comparar_distribuciones(x, x, ["a"]).iloc[0]
    assert d["delta_media_pct"] == 0 and d["delta_std_pct"] == 0
    assert d["intacta"]


def test_distribucion_desplazada_se_detecta():
    rng = np.random.default_rng(0)
    antes = pd.DataFrame({"a": rng.normal(50, 10, 500)})
    despues = pd.DataFrame({"a": rng.normal(70, 10, 500)})
    d = comparar_distribuciones(antes, despues, ["a"]).iloc[0]
    assert d["delta_media_pct"] > 30
    assert not d["intacta"]


def test_compara_ignorando_nulos_del_crudo():
    antes = pd.DataFrame({"a": [1.0, 2, np.nan, 3, 4]})
    despues = pd.DataFrame({"a": [1.0, 2, 2.5, 3, 4]})
    assert comparar_distribuciones(antes, despues, ["a"])["media_antes"].iloc[0] == 2.5


def test_delta_spearman_es_cero_si_no_cambia_nada():
    x = pd.DataFrame({"a": [1.0, 2, 3, 4], "b": [4.0, 1, 3, 2]})
    assert delta_spearman(x, x, ["a", "b"]) == 0


def test_verificar_reporta_el_control_que_falla():
    p = _procesado([10.0, 60], [50.0, 40])          # el segundo día tiene PM2.5 > PM10
    dist = pd.DataFrame({"intacta": [True, True]})
    v = verificar(p, dist, 0.01).set_index("control")
    assert v.loc["Claves únicas", "aprobado"]
    assert v.loc["Sin valores nulos", "aprobado"]
    assert not v.loc["Coherencia física de los sensores", "aprobado"]
    assert "50.0 %" in v.loc["Coherencia física de los sensores", "detalle"]


def test_verificar_detecta_claves_repetidas_y_nulos():
    p = _procesado([10.0, np.nan], [50.0, 50])
    p.loc[1, "Date"] = p.loc[0, "Date"]
    v = verificar(p, pd.DataFrame({"intacta": [True]}), 0.2).set_index("control")
    assert not v.loc["Claves únicas", "aprobado"]
    assert not v.loc["Sin valores nulos", "aprobado"]
    assert not v.loc["Correlaciones intactas", "aprobado"]

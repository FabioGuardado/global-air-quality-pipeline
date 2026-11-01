import numpy as np
import pytest

from air_quality.config import UMBRALES_OMS
from air_quality.severidad import METAS_OMS, N_NIVELES, clasificar, guia, niveles, nombres_niveles


@pytest.mark.parametrize("contaminante", list(METAS_OMS))
def test_metas_crecientes_y_guia_coherente_con_config(contaminante):
    valores = list(METAS_OMS[contaminante].values())
    assert valores == sorted(valores)
    assert guia(contaminante) == UMBRALES_OMS[contaminante]


@pytest.mark.parametrize("contaminante", list(METAS_OMS))
def test_niveles_contiguos(contaminante):
    nv = niveles(contaminante)
    assert nv[0].nombre == "Cumple guía" and np.isinf(nv[0].desde)
    assert np.isinf(nv[-1].hasta) and nv[-1].indice == N_NIVELES - 1
    for a, b in zip(nv, nv[1:]):
        assert a.hasta == b.desde
        assert a.indice < b.indice


def test_no2_salta_metas_inexistentes():
    assert [n.indice for n in niveles("NO2")] == [0, 1, 4, 5]
    assert nombres_niveles("NO2") == ["Cumple guía", "Sobre guía", "Sobre IT-2", "Sobre IT-1"]


@pytest.mark.parametrize("valor, esperado", [
    (5, "Cumple guía"), (15, "Cumple guía"), (15.01, "Sobre guía"), (25, "Sobre guía"),
    (30, "Sobre IT-4"), (37.5, "Sobre IT-4"), (40, "Sobre IT-3"), (60, "Sobre IT-2"),
    (75, "Sobre IT-2"), (75.01, "Sobre IT-1"), (500, "Sobre IT-1"),
])
def test_clasificar_pm25_limites_inclusivos(valor, esperado):
    assert clasificar([valor], "PM2.5").iloc[0] == esperado


def test_clasificar_es_ordenada_y_respeta_nulos():
    c = clasificar([10, np.nan, 100], "PM2.5")
    assert c.cat.ordered
    assert c.isna().tolist() == [False, True, False]
    assert c.iloc[0] < c.iloc[2]


def test_contaminante_sin_metas():
    with pytest.raises(KeyError, match="SO2"):
        niveles("SO2")


def test_rango_legible():
    assert [n.rango for n in niveles("PM2.5")][:2] == ["≤ 15", "15–25"]
    assert niveles("PM2.5")[-1].rango == "> 75"

import numpy as np
import pandas as pd
import pytest

from air_quality.bitacora import Bitacora
from air_quality.transformacion import (diagnostico_escalado, dummies_ciudad, elegir_escalador,
                                        escalar, vif)


def test_dummies_drop_first():
    df = pd.DataFrame({"City": ["a", "b", "c", "a"]})
    d = dummies_ciudad(df)
    assert list(d.columns) == ["city_b", "city_c"]
    assert dummies_ciudad(df, drop_first=False).sum(axis=1).eq(1).all()


def test_vif_independientes_cerca_de_uno_y_colineal_infinito():
    rng = np.random.default_rng(0)
    X = pd.DataFrame({"a": rng.normal(size=500), "b": rng.normal(size=500)})
    assert vif(X).max() < 1.1

    X["c"] = X["a"] + X["b"]
    assert np.isinf(vif(X)).all()


@pytest.mark.parametrize("fila, esperado", [
    ({"% outliers": 6, "IQR/std": 1.3, "p99/max": 0.99}, "RobustScaler"),
    ({"% outliers": 0, "IQR/std": 0.8, "p99/max": 0.99}, "RobustScaler"),
    ({"% outliers": 0, "IQR/std": 1.7, "p99/max": 0.99}, "MinMaxScaler"),
    ({"% outliers": 0, "IQR/std": 1.3, "p99/max": 0.5}, "StandardScaler"),
])
def test_elegir_escalador(fila, esperado):
    assert elegir_escalador(pd.Series(fila)) == esperado


def test_diagnostico_y_escalado_conservan_la_forma():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"uniforme": rng.uniform(0, 100, 1000),
                       "colas": rng.standard_t(2, 1000)})
    diag = diagnostico_escalado(df, ["uniforme", "colas"])
    assert diag.loc["uniforme", "escalador"] == "MinMaxScaler"
    assert diag.loc["colas", "escalador"] == "RobustScaler"

    bitacora = Bitacora()
    esc = escalar(df, diag, bitacora)
    assert esc["uniforme"].min() == pytest.approx(0) and esc["uniforme"].max() == pytest.approx(1)
    assert esc["colas"].median() == pytest.approx(0, abs=1e-9)
    # escalado lineal: la asimetría no cambia
    assert esc.skew().values == pytest.approx(df.skew().values)
    assert len(bitacora) == 2

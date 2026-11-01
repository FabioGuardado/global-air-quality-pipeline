import numpy as np
import pandas as pd

from air_quality.outliers import (consenso_outliers, flags_outliers, outliers_mahalanobis,
                                  resumen_outliers)


def _serie_con_atipico():
    rng = np.random.default_rng(0)
    s = pd.Series(rng.normal(50, 5, 500))
    s.iloc[0] = 500.0
    return s


def test_flags_marca_el_atipico_en_los_tres_criterios():
    f = flags_outliers(_serie_con_atipico())
    assert list(f.columns) == ["IQR", "Z", "MAD"]
    assert f.iloc[0].all()


def test_flags_con_mad_cero_no_divide_por_cero():
    s = pd.Series([1.0] * 20 + [2.0])
    f = flags_outliers(s)
    assert not f["MAD"].any()


def test_consenso_requiere_dos_criterios():
    df = pd.DataFrame({"x": _serie_con_atipico()})
    c = consenso_outliers(df, ["x"])
    assert c.loc[0, "x"]
    assert c["x"].sum() < 10


def test_resumen_outliers():
    df = pd.DataFrame({"x": _serie_con_atipico(), "y": np.linspace(0, 1, 500)})
    r = resumen_outliers(df, ["x", "y"])
    assert r.loc["y", "consenso (>=2)"] == 0
    assert r.loc["x", "consenso (>=2)"] >= 1


def test_mahalanobis_detecta_punto_multivariado():
    rng = np.random.default_rng(0)
    x = rng.normal(0, 1, 400)
    df = pd.DataFrame({"a": x, "b": x + rng.normal(0, 0.1, 400)})
    # cada coordenada es normal por separado, pero la combinación rompe la correlación
    df.loc[0] = [2.0, -2.0]
    out = outliers_mahalanobis(df, ["a", "b"])
    assert out.loc[0]
    assert out.mean() < 0.02

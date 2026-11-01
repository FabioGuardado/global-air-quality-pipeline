import numpy as np
import pandas as pd
import pytest

from air_quality.bitacora import Bitacora
from air_quality.imputacion import (aplicar_imputacion, columnas_con_nulos, plan_imputacion,
                                    validar_imputacion)


def _datos(n=200, seed=1):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "City": np.repeat(["a", "b"], n // 2),
        "x": rng.uniform(0, 100, n),
        "y": rng.uniform(0, 100, n),
        "sesgada": rng.lognormal(0, 1.2, n),
    })


def test_columnas_con_nulos():
    df = _datos()
    df.loc[0, "x"] = np.nan
    assert columnas_con_nulos(df, ["x", "y", "no_existe"]) == ["x"]


@pytest.mark.parametrize("col, frac, esperado", [
    ("x", 0.70, "eliminar_columna"),
    ("x", 0.02, "interpolacion"),
    ("x", 0.20, "media_ciudad"),
    ("sesgada", 0.20, "mediana_ciudad"),
])
def test_plan_reglas(col, frac, esperado):
    df = _datos()
    rng = np.random.default_rng(2)
    idx = rng.choice(len(df), int(len(df) * frac), replace=False)
    df.loc[idx, col] = np.nan
    plan = plan_imputacion(df, [col], ref_cols=["x", "y", "sesgada"])
    assert plan.loc[col, "estrategia"] == esperado


def test_plan_detecta_mar_con_correlacion_alta():
    df = _datos()
    df["x2"] = df["x"] * 2 + 1                     # r = 1 con x
    df["x3"] = df["x"] ** 1.5
    faltan = df["x"] > 70                          # el nulo de x2 depende de x
    df.loc[faltan, "x2"] = np.nan
    df.loc[df.index[:3], "x"] = np.nan
    df.loc[df.index[:3], "x3"] = np.nan
    plan = plan_imputacion(df, ["x2", "x", "x3"], ref_cols=["x", "x2", "x3", "y"])
    assert plan.loc["x2", "estrategia"] == "revisar_multivariada"


def test_interpolacion_por_ciudad_no_mezcla_ciudades():
    df = pd.DataFrame({"City": ["a", "a", "a", "b", "b", "b"],
                       "x": [1.0, np.nan, 3.0, 100.0, np.nan, 300.0]})
    plan = pd.DataFrame({"estrategia": ["interpolacion"], "motivo": ["test"]}, index=["x"])
    out = aplicar_imputacion(df, plan)
    assert out["x"].tolist() == [1.0, 2.0, 3.0, 100.0, 200.0, 300.0]


def test_imputacion_por_ciudad_y_respaldo_global():
    df = pd.DataFrame({"City": ["a", "a", "a", "b"],
                       "x": [1.0, 3.0, np.nan, np.nan]})   # b no tiene ningún valor
    plan = pd.DataFrame({"estrategia": ["mediana_ciudad"], "motivo": ["test"]}, index=["x"])
    bitacora = Bitacora()
    out = aplicar_imputacion(df, plan, bitacora)
    assert out["x"].tolist() == [1.0, 3.0, 2.0, 2.0]
    assert bitacora.decisiones[0]["accion"] == "mediana_ciudad (2 valores)"
    assert df["x"].isna().sum() == 2              # no muta la entrada


def test_eliminar_columna():
    df = _datos()
    plan = pd.DataFrame({"estrategia": ["eliminar_columna"], "motivo": ["70%"]}, index=["y"])
    assert "y" not in aplicar_imputacion(df, plan).columns


def test_estrategia_sin_imputador_falla_explicitamente():
    plan = pd.DataFrame({"estrategia": ["revisar_multivariada"], "motivo": ["MAR"]}, index=["x"])
    with pytest.raises(ValueError, match="revisar_multivariada"):
        aplicar_imputacion(_datos(), plan)


def test_validar_imputacion():
    antes = _datos()
    antes.loc[:3, "x"] = np.nan
    despues = antes.fillna({"x": antes["x"].median()})
    v = validar_imputacion(antes, despues, ["x"])
    assert bool(v.loc["x", "distribucion_intacta"])

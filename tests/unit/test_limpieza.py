import numpy as np
import pandas as pd
import pytest

from air_quality.bitacora import Bitacora
from air_quality.limpieza import (agregar_variables_tiempo, agregar_viento_cat,
                                  eliminar_duplicados, fechas_invalidas, normalizar_claves,
                                  normalizar_texto, perfilar, tipo_por_cardinalidad)


@pytest.mark.parametrize("entrada, esperado", [
    ("  São   Paulo ", "sao paulo"),
    ("BOGOTÁ", "bogota"),
    ("new\tyork", "new york"),
    ("lima", "lima"),
])
def test_normalizar_texto(entrada, esperado):
    assert normalizar_texto(entrada) == esperado


def test_normalizar_texto_respeta_nulos():
    assert normalizar_texto(np.nan) is np.nan


def test_tipo_por_cardinalidad():
    assert tipo_por_cardinalidad(pd.Series([1, 1, 1])) == "constante"
    assert tipo_por_cardinalidad(pd.Series(range(100))) == "posible identificador"
    assert tipo_por_cardinalidad(pd.Series(["a", "b"] * 50)) == "baja cardinalidad"
    assert tipo_por_cardinalidad(pd.Series(np.arange(200) % 50, dtype=float)) == "numérica continua"
    assert tipo_por_cardinalidad(pd.Series([f"c{i % 50}" for i in range(200)])) == "alta cardinalidad"


def test_perfilar_cuenta_nulos(crudo_sintetico):
    perfil = perfilar(crudo_sintetico)
    assert perfil.loc["PM2.5", "n_nulos"] == crudo_sintetico["PM2.5"].isna().sum()
    assert perfil.loc["Temperature", "n_nulos"] == 0


def test_fechas_invalidas_distingue_formato():
    fechas = pd.Series(["1/13/2023", "12/31/2023"])
    assert fechas_invalidas(fechas, "%m/%d/%Y") == 0
    assert fechas_invalidas(fechas, "%d/%m/%Y") == 2


def test_normalizar_claves(crudo_sintetico):
    bitacora = Bitacora()
    df = normalizar_claves(crudo_sintetico, bitacora)

    assert set(df["City"]) == {"madrid", "mexico city", "paris"}
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert df["Date"].isna().sum() == 0
    assert df["Date"].min() == pd.Timestamp("2023-01-01")
    assert len(bitacora) == 3
    # no muta la entrada
    assert crudo_sintetico["Date"].dtype == object


def test_variables_tiempo():
    df = pd.DataFrame({"Date": pd.to_datetime(["2023-01-06", "2023-01-07", "2023-01-08"])})
    out = agregar_variables_tiempo(df)
    assert out["dia_semana"].tolist() == [4, 5, 6]
    assert out["fin_semana"].tolist() == [False, True, True]
    assert out["mes"].tolist() == [1, 1, 1]


def test_viento_cat_en_cuartiles():
    df = pd.DataFrame({"Wind Speed": np.arange(1, 9, dtype=float)})
    out = agregar_viento_cat(df)
    assert out["viento_cat"].value_counts().tolist() == [2, 2, 2, 2]
    assert out["viento_cat"].iloc[0] == "muy bajo" and out["viento_cat"].iloc[-1] == "alto"


def test_eliminar_duplicados_conserva_el_mas_completo(crudo_sintetico):
    df = normalizar_claves(crudo_sintetico)
    bitacora = Bitacora()
    limpio = eliminar_duplicados(df, bitacora=bitacora)

    assert len(limpio) == 120
    assert not limpio.duplicated(subset=["City", "Country", "Date"]).any()
    # la fila 10 original (con PM2.5) sobrevive y la copia sin PM2.5 se descarta
    original = df.iloc[10]
    fila = limpio[(limpio["City"] == original["City"]) & (limpio["Date"] == original["Date"])]
    assert fila["PM2.5"].iloc[0] == original["PM2.5"]
    assert [d["accion"] for d in bitacora.decisiones] == ["Eliminar 3 filas", "Eliminar 1 filas"]

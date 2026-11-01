"""Pipeline completo sobre el dataset real y sobre uno sintético."""

import numpy as np
import pandas as pd
import pytest

from air_quality import cargar_crudo, cargar_procesado, config, ejecutar
from air_quality.pipeline import main


@pytest.fixture(scope="module")
def resultado_real():
    return ejecutar(cargar_crudo())


def test_reproduce_el_csv_versionado(resultado_real, tmp_path):
    """El entregable de data/processed debe poder regenerarse exactamente desde el crudo."""
    salida = tmp_path / "procesado.csv"
    resultado_real.procesado.to_csv(salida, index=False)
    esperado = config.PROCESSED_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert salida.read_text(encoding="utf-8").replace("\r\n", "\n") == esperado


def test_contrato_del_procesado(resultado_real):
    df = resultado_real.procesado
    assert list(df.columns) == config.ENTREGABLE
    assert len(df) >= 5000                                   # mínimo de la rúbrica
    assert df.isna().sum().sum() == 0
    assert not df.duplicated(subset=config.CLAVES).any()
    assert (df.groupby("City")["Country"].nunique() == 1).all()
    assert df["n_excedencias_oms"].between(0, 3).all()
    assert (df[config.POLL] >= 0).all().all()
    assert df.equals(df.sort_values(["City", "Date"]).reset_index(drop=True))


def test_matriz_de_modelado(resultado_real):
    modelo = resultado_real.modelo
    final = resultado_real.final
    assert modelo.isna().sum().sum() == 0
    assert not set(config.EXCLUIR_MODELO) & set(modelo.columns)
    escaladas = list(resultado_real.diagnostico_escalado.index)
    # escalado lineal: la forma de cada distribución se conserva
    assert np.allclose(modelo[escaladas].skew(), final[escaladas].skew())
    assert np.allclose(modelo[escaladas].kurt(), final[escaladas].kurt())


def test_bitacora_documenta_cada_fase(resultado_real):
    fases = set(resultado_real.bitacora.to_frame()["fase"])
    assert fases == {"I-claves", "III-duplicados", "III-nulos", "IV"}


def test_cargar_procesado_restaura_tipos():
    df = cargar_procesado()
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert isinstance(df["City"].dtype, pd.CategoricalDtype)
    assert df["fin_semana"].dtype == bool


def test_pipeline_sobre_dataset_sintetico(crudo_sintetico):
    r = ejecutar(crudo_sintetico)
    assert len(r.procesado) == 120
    assert set(r.procesado["City"]) == {"lima", "sao paulo", "paris"}
    assert r.procesado.isna().sum().sum() == 0


def test_cli_escribe_el_csv(crudo_sintetico, tmp_path, capsys):
    entrada = tmp_path / "crudo.csv"
    salida = tmp_path / "sub" / "procesado.csv"
    crudo_sintetico.to_csv(entrada, index=False)

    main(["--entrada", str(entrada), "--salida", str(salida)])

    assert salida.exists()
    assert len(pd.read_csv(salida)) == 120
    assert "120 filas" in capsys.readouterr().out

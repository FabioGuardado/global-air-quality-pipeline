"""Ejecuta el notebook de punta a punta (lento: ~30 s).

El propio notebook verifica en la Fase V que su entregable coincide con `ejecutar()`.
"""

import pytest

from air_quality.config import ROOT

nbformat = pytest.importorskip("nbformat")
nbclient = pytest.importorskip("nbclient")

NOTEBOOK = ROOT / "notebooks" / "eda_pipeline.ipynb"


@pytest.mark.slow
def test_notebook_se_ejecuta_sin_errores(tmp_path, monkeypatch):
    monkeypatch.setenv("MPLBACKEND", "Agg")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    # Se ejecuta en una copia: el CSV de salida se redirige para no tocar data/processed
    for celda in nb.cells:
        if celda.cell_type == "code" and "SALIDA = PROCESSED_PATH" in celda.source:
            celda.source = celda.source.replace(
                "SALIDA = PROCESSED_PATH", f"SALIDA = __import__('pathlib').Path(r'{tmp_path}') / 'out.csv'")
    nbclient.NotebookClient(nb, timeout=600, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
    assert (tmp_path / "out.csv").exists()

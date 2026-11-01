import sys

import pytest

from air_quality.config import ROOT

APP_DIR = ROOT / "app"
sys.path.insert(0, str(APP_DIR))


@pytest.fixture(scope="session")
def datos():
    from air_quality import cargar_procesado
    return cargar_procesado()


@pytest.fixture(scope="session", autouse=True)
def plantillas():
    import tema
    tema.registrar_plantillas()

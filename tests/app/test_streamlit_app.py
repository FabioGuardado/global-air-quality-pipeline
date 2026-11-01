"""Tests de humo e interacción de la app con streamlit.testing (sin navegador)."""

import pytest
from streamlit.testing.v1 import AppTest

from air_quality.config import ROOT

APP = str(ROOT / "app" / "streamlit_app.py")


@pytest.fixture
def app():
    return AppTest.from_file(APP, default_timeout=60).run()


def _texto(at):
    """Todo el HTML/markdown renderizado, para buscar los títulos dinámicos."""
    return " ".join(e.proto.body for e in at.get("html"))


def test_carga_sin_errores(app):
    assert not app.exception
    assert len(app.get("plotly_chart")) == 2
    assert "9 de cada 10 días" in _texto(app)


def test_region_restringe_las_ciudades(app):
    app.multiselect(key="f_regiones").set_value(["Oceanía"]).run()
    assert app.multiselect(key="f_ciudades").options == ["Sydney"]


def test_cambiar_region_descarta_ciudades_fuera_de_ella(app):
    app.multiselect(key="f_ciudades").set_value(["madrid", "tokyo"]).run()
    app.multiselect(key="f_regiones").set_value(["Asia"]).run()
    assert app.session_state["f_ciudades"] == ["tokyo"]
    assert not app.exception


def test_filtro_de_ciudad_actualiza_el_texto(app):
    app.multiselect(key="f_ciudades").set_value(["tokyo"]).run()
    assert not app.exception
    assert "En Tokyo" in _texto(app)


@pytest.mark.parametrize("cont", ["PM10", "NO2"])
def test_cambiar_contaminante(app, cont):
    app.multiselect(key="f_niveles").set_value(["Sobre IT-1"]).run()
    app.session_state["f_cont"] = cont
    app.run()
    assert not app.exception


def test_contaminante_con_menos_niveles_limpia_niveles_invalidos(app):
    app.multiselect(key="f_niveles").set_value(["Sobre IT-3"]).run()
    # simula el callback del control segmentado
    import filtros  # noqa: F401  (app/ ya está en sys.path)
    app.session_state["f_cont"] = "NO2"
    app.run()
    assert not app.exception


def test_filtros_sin_resultados_muestran_estado_vacio(app, datos):
    # un día en el que Sydney (única ciudad de Oceanía) no tiene medición
    con_sydney = set(datos.loc[datos["City"] == "sydney", "Date"])
    dia = next(d for d in sorted(datos["Date"].unique()) if d not in con_sydney).date()
    app.multiselect(key="f_regiones").set_value(["Oceanía"])
    app.date_input(key="f_fechas").set_value((dia, dia))
    app.run()
    assert not app.exception
    assert "Sin datos para esta combinación" in _texto(app)
    assert len(app.get("plotly_chart")) == 0


def test_limpiar_restablece_filtros(app):
    app.multiselect(key="f_ciudades").set_value(["tokyo"]).run()
    app.button[0].click().run()
    assert app.session_state["f_ciudades"] == []


def test_modo_oscuro(app):
    app.toggle(key="oscuro").set_value(True).run()
    assert not app.exception
    assert "#0d0d0d" in _texto(app)        # el CSS oscuro está inyectado

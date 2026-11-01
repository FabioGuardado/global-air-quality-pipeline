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


def _ir(app, pagina):
    return app.switch_page(f"paginas/{pagina}.py").run()


PAGINAS = {  # página → (gráficos, frase del título)
    "diagnostico": (2, "9 de cada 10 días"),
    "patrones": (4, "No hay temporada limpia"),
    "causa": (2, "Ni el viento, el calor ni el fin de semana"),
    "recomendacion": (3, "Cumplir la guía exige recortar un 90 %"),
}


def test_inicio_es_el_diagnostico_con_cabecera_completa(app):
    assert not app.exception
    texto = _texto(app)
    assert "9 de cada 10 días" in texto
    assert "El aire que respiran 20 ciudades" in texto
    assert len(app.get("plotly_chart")) == 2


@pytest.mark.parametrize("pagina", list(PAGINAS))
def test_cada_capitulo_es_una_pagina(app, pagina):
    _ir(app, pagina)
    assert not app.exception
    n_graficos, titulo = PAGINAS[pagina]
    texto = _texto(app)
    assert titulo in texto
    assert len(app.get("plotly_chart")) == n_graficos
    # la cabecera completa solo aparece en el 01
    assert ("El aire que respiran 20 ciudades" in texto) == (pagina == "diagnostico")
    assert "Vista" in texto


def test_filtros_persisten_entre_paginas(app):
    app.multiselect(key="f_ciudades").set_value(["tokyo"]).run()
    _ir(app, "causa")
    assert app.session_state["f_ciudades"] == ["tokyo"]
    assert "Tokyo" in _texto(app)


def test_vista_resalta_los_filtros_activos(app):
    assert 'class="on"' not in _texto(app)
    app.multiselect(key="f_ciudades").set_value(["tokyo"]).run()
    assert '<b class="on">Tokyo</b>' in _texto(app)


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
    for pagina in PAGINAS:
        _ir(app, pagina)
        assert not app.exception
        assert "Sin datos para esta combinación" in _texto(app)
        assert len(app.get("plotly_chart")) == 0


def test_limpiar_restablece_filtros(app):
    app.multiselect(key="f_ciudades").set_value(["tokyo"]).run()
    app.button(key="btn_limpiar").click().run()
    assert app.session_state["f_ciudades"] == []


def test_modo_oscuro(app):
    app.button(key="btn_tema").click().run()
    assert app.session_state["oscuro"]
    assert not app.exception
    assert "#0d0d0d" in _texto(app)        # el CSS oscuro está inyectado


@pytest.mark.parametrize("detalle", ["Estación", "Fin de semana", "Ciudad"])
def test_detalle_de_causa(app, detalle):
    _ir(app, "causa")
    app.segmented_control(key="det_causa").set_value(detalle).run()
    assert not app.exception


def test_una_ciudad_deja_ciudad_como_no_aplica(app):
    app.multiselect(key="f_ciudades").set_value(["tokyo"]).run()
    _ir(app, "causa")
    app.segmented_control(key="det_causa").set_value("Ciudad").run()
    assert not app.exception
    assert "Con una sola ciudad seleccionada" in _texto(app)


@pytest.mark.parametrize("reduccion", [0, 50, 95])
def test_simulador(app, reduccion):
    _ir(app, "recomendacion")
    app.slider(key="sim_reduccion").set_value(reduccion).run()
    assert not app.exception
    texto = _texto(app)
    if reduccion == 0:
        assert "todavía no alcanza ninguna meta" in texto
    elif reduccion == 95:
        assert "se cumple la guía de la OMS" in texto
    else:
        assert "se alcanza <b>IT-1</b>" in texto


def test_tabla_de_detalle_y_descarga(app, datos):
    app.multiselect(key="f_ciudades").set_value(["tokyo"]).run()
    _ir(app, "recomendacion")
    assert not app.exception
    texto = _texto(app)
    n = int((datos["City"] == "tokyo").sum())
    assert f"<b>{n:,}</b> mediciones" in texto
    assert "Seleccionada: <b>Tokyo</b>" in texto


def test_pagina_de_auditoria(app):
    _ir(app, "auditoria")
    assert not app.exception
    texto = _texto(app)
    assert "Auditoría del dato" in texto
    assert "4 de 5 controles aprobados" in texto
    assert "Coherencia física de los sensores" in texto
    assert len(app.get("plotly_chart")) == 2
    assert '<div class="activos">' not in texto   # los filtros no aplican al anexo


def test_bitacora_filtrable_por_fase(app):
    _ir(app, "auditoria")
    app.segmented_control(key="aud_fase").set_value("Duplicados").run()
    assert not app.exception
    texto = _texto(app)
    assert "Eliminar 13897 filas" in texto
    assert "Normalizar texto" not in texto


def test_el_04_lleva_al_anexo(app):
    _ir(app, "recomendacion")
    assert "Ver de dónde salen los datos" in str([e.proto for e in app.get("page_link")])

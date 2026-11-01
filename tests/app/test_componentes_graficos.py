import numpy as np
import pytest

import componentes as ui
import graficos
import tema
from air_quality.metricas import distribucion_niveles, por_ciudad
from air_quality.severidad import niveles
from filtros import ciudad_de_seleccion


@pytest.fixture(params=[tema.CLARO, tema.OSCURO], ids=["claro", "oscuro"])
def t(request):
    return request.param


def test_barras_un_trazo_por_nivel_y_colores_de_la_rampa(datos, t):
    fig = graficos.barras_niveles(distribucion_niveles(datos), por_ciudad(datos), "PM2.5", t)
    barras = [tr for tr in fig.data if tr.type == "bar"]
    assert [b.name for b in barras] == [n.nombre for n in niveles("PM2.5")]
    assert [b.marker.color for b in barras] == list(t.severidad)
    assert len(fig.layout.annotations) == 20           # etiqueta directa por ciudad
    assert fig.layout.xaxis.range == (0, 100)          # eje completo, sin truncar


def test_barras_ordenadas_por_tramo_mas_severo(datos, t):
    dist = distribucion_niveles(datos)
    fig = graficos.barras_niveles(dist, por_ciudad(datos), "PM2.5", t)
    severo = fig.data[-1]
    assert list(severo.x) == sorted(severo.x)          # Plotly dibuja de abajo hacia arriba


def test_barras_atenuan_lo_no_seleccionado(datos, t):
    fig = graficos.barras_niveles(distribucion_niveles(datos), por_ciudad(datos), "PM2.5", t,
                                  seleccion=("tokyo",))
    opacidad = dict(zip(fig.data[0].y, fig.data[0].marker.opacity))
    assert opacidad["Tokyo"] == 1 and opacidad["Madrid"] < 1


def test_no2_usa_indices_globales_de_color(datos, t):
    fig = graficos.barras_niveles(distribucion_niveles(datos, "NO2"), por_ciudad(datos, "NO2"),
                                  "NO2", t)
    colores = [tr.marker.color for tr in fig.data if tr.type == "bar"]
    assert colores == [t.severidad[i] for i in (0, 1, 4, 5)]


def test_mapa_dominio_de_color_fijo(datos, t):
    fig = graficos.mapa_ciudades(por_ciudad(datos), "PM2.5", t)
    m = fig.data[0].marker
    assert (m.cmin, m.cmax) == (0, 150)               # 2 × IT-1, no el rango observado
    assert len(fig.data[0].lat) == 20


def test_mapa_resalta_seleccion(datos, t):
    resumen = por_ciudad(datos)
    fig = graficos.mapa_ciudades(resumen, "PM2.5", t, seleccion=("tokyo",))
    anillos = dict(zip(resumen["City"], fig.data[0].marker.line.color))
    assert anillos["tokyo"] == t.acento and anillos["madrid"] == t.superficie


def test_ciudad_de_seleccion():
    estado = {"selection": {"points": [{"customdata": ["Tokyo", "x", "tokyo"]}]}}
    assert ciudad_de_seleccion(estado, 2) == "tokyo"
    assert ciudad_de_seleccion({"selection": {"points": []}}, 2) is None
    assert ciudad_de_seleccion(None, 2) is None


def test_formatos():
    assert ui.fmt_pct(93.162) == "93.2"
    assert ui.fmt_pct(np.nan) == "—"
    assert ui.delta_pp(94.4, 93.2) == "▲ 1.2 pp vs. total"
    assert ui.delta_pp(93.2, 93.2) == ""
    assert ui.fecha(__import__("pandas").Timestamp("2023-12-28")) == "28 dic 2023"


def test_css_expone_tokens_de_cada_tema(t):
    css = tema.css(t)
    assert t.superficie in css and t.severidad[5] in css
    assert ("stBaseButton" in css) == (t is tema.OSCURO)   # overrides solo en oscuro

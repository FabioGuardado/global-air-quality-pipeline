"""Piezas de UI en HTML propio. Todas usan las variables CSS de `tema.css()`."""

from html import escape

import numpy as np
import streamlit as st

CAPITULOS = [
    ("01", "diagnostico", "Diagnóstico"),
    ("02", "patrones", "Patrones y anomalías"),
    ("03", "causa", "Causa raíz"),
    ("04", "recomendacion", "Recomendación"),
]


def html(contenido: str):
    st.html(contenido)


def fmt_pct(x, dec=1):
    return "—" if x is None or np.isnan(x) else f"{x:.{dec}f}"


def fmt_num(x, dec=1):
    return "—" if x is None or np.isnan(x) else f"{x:,.{dec}f}"


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha(d):
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def delta_pp(actual, global_, invertido=False):
    """Texto de diferencia en puntos porcentuales contra el total (vacío si no hay filtro)."""
    if actual is None or global_ is None or np.isnan(actual) or abs(actual - global_) < 0.05:
        return ""
    d = actual - global_
    flecha = "▲" if d > 0 else "▼"
    return f"{flecha} {abs(d):.1f} pp vs. total"


def encabezado(n_filas, n_ciudades, desde, hasta):
    html(f"""
<header class="cab">
  <div>
    <div class="marca"><span class="punto"></span>Calidad del aire global · 2023</div>
    <h1>El aire que respiran 20 ciudades no da tregua</h1>
    <p class="tesis">Un recorrido en cuatro pasos por {n_filas:,} mediciones diarias: cuánto se
    incumplen las guías de la OMS, dónde y cuándo aparecen los episodios, qué explica (y qué no) la
    contaminación y qué decisiones se desprenden de la evidencia.</p>
  </div>
  <div class="meta">
    <b>{n_ciudades}</b> ciudades · <b>6</b> regiones<br>
    <b>{fecha(desde)}</b> — <b>{fecha(hasta)}</b><br>
    Fuente: dataset global de calidad del aire,<br>procesado en la Fase I del proyecto
  </div>
</header>""")


def navegacion(disponibles=("01",)):
    items = []
    for num, ancla, nombre in CAPITULOS:
        if num in disponibles:
            items.append(f'<a href="#{ancla}" target="_self"><span class="num">{num}</span>{nombre}</a>')
        else:
            items.append(f'<span class="pendiente"><span class="num">{num}</span>{nombre}</span>')
    html(f'<nav class="nav-cap">{"".join(items)}</nav>')


def capitulo(num, ancla, kicker, titulo, bajada=""):
    html(f"""
<section class="capitulo" id="{ancla}">
  <div class="num">{num}</div>
  <div>
    <div class="kicker">{escape(kicker)}</div>
    <h2>{titulo}</h2>
    {f'<p class="bajada">{bajada}</p>' if bajada else ''}
  </div>
</section>""")


def hero(cifra, unidad, texto, rotulo, progreso, delta="", escala=("0 %", "100 %")):
    relleno = 0 if progreso is None or np.isnan(progreso) else max(0, min(progreso, 100))
    html(f"""
<div class="hero">
  <div>
    <div class="rotulo">{rotulo}</div>
    <div class="cifra">{cifra}<small>{unidad}</small></div>
    <div class="texto">{texto}</div>
    <div class="delta">{delta}</div>
  </div>
  <div class="medidor" role="img" aria-label="{relleno:.1f} por ciento">
    <div class="pista"><div class="relleno" style="width:{relleno:.2f}%"></div></div>
    <div class="escala"><span>{escala[0]}</span><span>{escala[1]}</span></div>
  </div>
</div>""")


def kpis(tarjetas):
    """tarjetas: lista de dict(rotulo, valor, unidad, nota, delta, color)."""
    bloques = []
    for k in tarjetas:
        marca = (f'<i class="marca-sev" style="background:{k["color"]}"></i>'
                 if k.get("color") else "")
        bloques.append(f"""
<div class="kpi">
  <div class="rotulo">{marca}{k['rotulo']}</div>
  <div class="valor">{k['valor']}<small>{k.get('unidad', '')}</small></div>
  <div class="nota">{k.get('nota', '')}</div>
  <div class="delta">{k.get('delta', '')}</div>
</div>""")
    html(f'<div class="kpis">{"".join(bloques)}</div>')


def titulo_grafico(titulo, sub=""):
    html(f'<div class="titulo-graf">{titulo}</div>' + (f'<p class="sub-graf">{sub}</p>' if sub else ""))


def nota(texto):
    html(f'<p class="nota-graf">{texto}</p>')


def leyenda_severidad(niveles, colores):
    items = "".join(f'<span><i style="background:{colores[n.indice]}"></i>{n.nombre} '
                    f'<em>{n.rango}</em></span>' for n in niveles)
    html(f'<div class="leyenda-sev" role="list">{items}</div>')


def vacio(mensaje="Ningún registro cumple todos los filtros activos.",
          ayuda="Amplía el rango de fechas o quita algún filtro."):
    html(f'<div class="vacio"><b>{mensaje}</b>{ayuda}</div>')

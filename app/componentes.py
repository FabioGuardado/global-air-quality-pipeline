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


def subseccion(kicker, titulo, texto=""):
    html(f'''<div class="subseccion"><div class="kicker">{kicker}</div><h3>{titulo}</h3>
{f'<p>{texto}</p>' if texto else ''}</div>''')


def tabla_episodios(ep, contaminante, colores, nombre_nivel, n=8):
    """Tabla HTML de los peores episodios con chip de nivel OMS."""
    filas = []
    for _, e in ep.head(n).iterrows():
        nivel, indice = nombre_nivel(e["valor"])
        filas.append(f"""<tr><td>{escape(nombre_ciudad(e['City']))}</td>
<td class="num">{fecha(e['Date'])}</td><td class="num"><b>{e['valor']:.1f}</b></td>
<td class="num">{e['veces_mediana']:.1f}×</td>
<td><span class="chip"><i style="background:{colores[indice]}"></i>{nivel}</span></td></tr>""")
    html(f"""<table class="tabla"><thead><tr><th>Ciudad</th><th class="num">Fecha</th>
<th class="num">{contaminante} <span class="unidad">µg/m³</span></th><th class="num">vs. su mediana</th><th>Nivel OMS</th></tr></thead>
<tbody>{''.join(filas)}</tbody></table>""")


def tabla_simple(df, alto_max=360):
    """Tabla HTML con scroll (st.dataframe no respeta el CSS del modo oscuro)."""
    cab = "".join(f'<th class="{"num" if df[c].dtype.kind in "if" else ""}">{escape(str(c))}</th>'
                  for c in df.columns)
    filas = "".join(
        "<tr>" + "".join(f'<td class="{"num" if df[c].dtype.kind in "if" else ""}">{escape(str(v))}</td>'
                         for c, v in zip(df.columns, fila)) + "</tr>"
        for fila in df.itertuples(index=False))
    html(f'<div class="tabla-scroll" style="max-height:{alto_max}px"><table class="tabla">'
         f'<thead><tr>{cab}</tr></thead><tbody>{filas}</tbody></table></div>')


def tarjeta_texto(rotulo, titulo, cuerpo, pie=""):
    html(f"""<div class="tarjeta-texto"><div class="rotulo">{rotulo}</div><h4>{titulo}</h4>
<div class="cuerpo">{cuerpo}</div>{f'<div class="pie">{pie}</div>' if pie else ''}</div>""")


def nombre_ciudad(c):
    return str(c).title()

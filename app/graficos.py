"""Constructores de figuras Plotly. Reciben datos ya agregados y un `Tema`; no leen estado de UI."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from air_quality.metricas import nombre_ciudad
from air_quality.severidad import guia, niveles

from tema import FUENTE, Tema, escala_secuencial

CONFIG = {"displayModeBar": False, "responsive": True, "scrollZoom": False}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def _eje_meses(fechas):
    """Marcas en el día 1 de cada mes con nombres en español (Plotly en Streamlit solo trae inglés)."""
    fechas = pd.to_datetime(pd.Series(fechas)).dropna()
    if fechas.empty:
        return {}
    inicio = fechas.min().to_period("M").to_timestamp()
    marcas = pd.date_range(inicio, fechas.max(), freq="MS")
    return dict(tickvals=list(marcas), ticktext=[MESES[m.month - 1] for m in marcas],
                hoverformat="%d/%m/%Y")


def _base(fig, t: Tema, alto):
    # Streamlit reemplaza fondos transparentes y la fuente con los de su tema aunque se use
    # theme=None, así que se fijan explícitamente.
    fig.update_layout(template=f"aire_{t.nombre}", height=alto,
                      paper_bgcolor=t.superficie, plot_bgcolor=t.superficie,
                      font=dict(family=FUENTE, color=t.tinta_2))
    return fig


def mapa_ciudades(resumen, contaminante, t: Tema, seleccion=(), alto=430):
    """Puntos por ciudad coloreados por la mediana del contaminante.

    El dominio del color es fijo (0 → 2 × IT-1) para no exagerar diferencias pequeñas entre
    ciudades: si todas están altas, el mapa debe verse uniformemente alto.
    """
    tope = niveles(contaminante)[-1].desde * 2
    g = guia(contaminante)
    sel = set(seleccion)
    anillo = [t.acento if c in sel else t.superficie for c in resumen["City"]]
    ancho = [3 if c in sel else 1.5 for c in resumen["City"]]
    custom = np.stack([
        resumen["City"].map(nombre_ciudad), resumen["Country"].str.title(),
        resumen["region"].astype(str), resumen["n"], resumen["mediana"],
        resumen["multiplo_guia"], resumen["pct_sobre_guia"], resumen["pct_criticos"],
        resumen["City"],
    ], axis=-1)
    fig = go.Figure(go.Scattergeo(
        lat=resumen["lat"], lon=resumen["lon"], mode="markers",
        marker=dict(size=17, color=resumen["mediana"], cmin=0, cmax=tope,
                    colorscale=escala_secuencial(t), line=dict(color=anillo, width=ancho),
                    colorbar=dict(title=dict(text=f"Mediana de {contaminante} (µg/m³)",
                                             font=dict(size=11, color=t.tenue)),
                                  tickvals=[g, tope / 2, tope],
                                  ticktext=[f"guía {g:g}", f"{tope / 2:g}", f"{tope:g}"],
                                  orientation="h", x=0.5, xanchor="center", y=-0.02,
                                  yanchor="top", len=0.7, thickness=8,
                                  title_side="top")),
        customdata=custom,
        hovertemplate=("<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
                       "<span style='color:" + t.tenue + "'>%{customdata[2]} · %{customdata[3]} días</span><br><br>"
                       f"Mediana {contaminante}: <b>%{{customdata[4]:.1f}} µg/m³</b> "
                       "(%{customdata[5]:.1f}× la guía)<br>"
                       "Días sobre la guía: <b>%{customdata[6]:.1f} %</b><br>"
                       "Días críticos (3 guías): %{customdata[7]:.1f} %<extra></extra>"),
    ))
    fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=False,
                    showcountries=True, countrycolor=t.pagina, countrywidth=0.6,
                    showland=True, landcolor=t.tierra, showocean=True, oceancolor=t.agua,
                    showlakes=False, bgcolor="rgba(0,0,0,0)", lataxis_range=[-50, 70],
                    lonaxis_range=[-130, 160])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=56), clickmode="event+select")
    return _base(fig, t, alto)


def barras_niveles(dist, resumen, contaminante, t: Tema, seleccion=(), alto=None):
    """Barra apilada al 100 % por ciudad con los días en cada nivel OMS.

    Ordenadas por % de días sobre IT-1 (el tramo más severo queda alineado a la derecha y se
    compara por longitud desde un eje común). Etiqueta directa: % de días sobre la guía.
    """
    nv = niveles(contaminante)
    severo = nv[-1].nombre
    orden = (dist[dist["nivel"] == severo].sort_values("pct")["City"].tolist())
    sel = set(seleccion)
    fig = go.Figure()
    for n in nv:
        d = dist[dist["nivel"] == n.nombre].set_index("City").reindex(orden)
        opacidad = [1 if not sel or c in sel else 0.28 for c in orden]
        fig.add_bar(
            y=[nombre_ciudad(c) for c in orden], x=d["pct"], orientation="h", name=n.nombre,
            marker=dict(color=t.severidad[n.indice], opacity=opacidad,
                        line=dict(color=t.superficie, width=1)),
            customdata=np.stack([d["n"], [n.rango] * len(orden), orden], axis=-1),
            hovertemplate=(f"<b>%{{y}}</b><br>{n.nombre} ({contaminante} %{{customdata[1]}} µg/m³)<br>"
                           "<b>%{x:.1f} %</b> de los días · %{customdata[0]} días<extra></extra>"),
        )
    sobre = resumen.set_index("City").reindex(orden)["pct_sobre_guia"]
    for c, v in zip(orden, sobre):
        fig.add_annotation(x=1, xref="paper", xanchor="left", xshift=8, y=nombre_ciudad(c),
                           text=f"{v:.0f} %", showarrow=False,
                           font=dict(color=t.tinta_2, size=12))
    filas = len(orden)
    fig.update_layout(
        barmode="stack", bargap=0.28, showlegend=False,
        xaxis=dict(range=[0, 100], showgrid=True, tickvals=[0, 25, 50, 75, 100],
                   ticktext=["0 %", "25 %", "50 %", "75 %", "100 %"], side="top"),
        yaxis=dict(tickfont=dict(color=t.tinta_2, size=12.5)),
        margin=dict(l=8, r=52, t=24, b=4), clickmode="event+select",
    )
    return _base(fig, t, alto or max(260, 26 * filas + 50))


# ============================== Capítulo 02 ==============================

def _lineas_referencia(fig, contaminante, t: Tema):
    """Guía OMS (discontinua) e IT-1 (punteada), rotuladas en el extremo derecho."""
    nv = niveles(contaminante)
    for valor, texto, guion in [(guia(contaminante), f"Guía OMS {guia(contaminante):g}", "dash"),
                                (nv[-1].desde, f"IT-1 {nv[-1].desde:g}", "dot")]:
        fig.add_hline(y=valor, line=dict(color=t.tinta_2, width=1, dash=guion),
                      annotation=dict(text=texto, font=dict(size=11, color=t.tinta_2)),
                      annotation_position="top left")


def calendario(cal, contaminante, t: Tema, orden, seleccion=()):
    """Mapa de calor ciudad × semana con la mediana semanal (dominio fijo 0 → 2 × IT-1)."""
    tope = niveles(contaminante)[-1].desde * 2
    g = guia(contaminante)
    piv = cal.pivot(index="City", columns="semana", values="mediana").reindex(orden)
    n = cal.pivot(index="City", columns="semana", values="n").reindex(orden)
    sel = set(seleccion)
    etiquetas = [f"<b>{nombre_ciudad(c)}</b>" if c in sel else nombre_ciudad(c) for c in orden]
    nombres = np.array([[nombre_ciudad(c)] * piv.shape[1] for c in orden], dtype=object)
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=piv.columns, y=etiquetas, zmin=0, zmax=tope,
        colorscale=escala_secuencial(t), xgap=2, ygap=2, hoverongaps=False,
        customdata=np.dstack([n.values.astype(object), nombres]),
        colorbar=dict(title=dict(text=f"Mediana semanal de {contaminante} (µg/m³)", side="top",
                                 font=dict(size=11, color=t.tenue)),
                      orientation="h", x=1, xanchor="right", y=1.0, yanchor="top",
                      len=0.32, thickness=8, tickvals=[g, tope / 2, tope],
                      ticktext=[f"guía {g:g}", f"{tope / 2:g}", f"{tope:g}"]),
        hovertemplate=("<b>%{customdata[1]}</b><br>Semana del %{x|%d/%m/%Y}<br>"
                       f"Mediana {contaminante}: <b>%{{z:.1f}} µg/m³</b><br>"
                       "%{customdata[0]} días medidos<extra></extra>"),
    ))
    # La barra de color va dentro del lienzo, en una franja reservada sobre el mapa: fuera de él,
    # el auto-margen de Plotly dejaba ~30 px vacíos entre el subtítulo y la barra.
    alto = 24 * len(orden) + 100
    franja = 70 / alto
    fig.update_layout(
        yaxis=dict(autorange="reversed", tickfont=dict(size=12, color=t.tinta_2), domain=[0, 1 - franja]),
        xaxis=dict(showgrid=False, **_eje_meses(piv.columns)),
        margin=dict(l=8, r=8, t=0, b=8),
    )
    return _base(fig, t, alto)


def tendencia(movil, banda, contaminante, t: Tema, seleccion=(), episodios=None, alto=380):
    """Media móvil de 7 días: banda p25–p75 entre ciudades + énfasis en las seleccionadas."""
    fig = go.Figure()
    fig.add_scatter(x=banda["Date"], y=banda["p75"], mode="lines", line=dict(width=0),
                    hoverinfo="skip", showlegend=False)
    fig.add_scatter(x=banda["Date"], y=banda["p25"], mode="lines", line=dict(width=0),
                    fill="tonexty", fillcolor=t.contexto, hoverinfo="skip", showlegend=False)
    sel = list(seleccion)[:3]
    fig.add_scatter(x=banda["Date"], y=banda["p50"], mode="lines",
                    line=dict(color=t.tenue if sel else t.acento, width=1.4 if sel else 2),
                    name="Mediana de las ciudades",
                    hovertemplate="Mediana entre ciudades: <b>%{y:.1f}</b> µg/m³<extra></extra>")
    if not sel and not banda.empty:
        fig.add_annotation(x=banda["Date"].iloc[-1], y=banda["p50"].iloc[-1],
                           text="Mediana de<br>las ciudades", xanchor="left", xshift=6,
                           showarrow=False, align="left", font=dict(size=11, color=t.tinta))
    tope = niveles(contaminante)[-1].desde * 2
    for i, c in enumerate(sel):
        s = movil[movil["City"] == c].dropna(subset=["movil"])
        color = t.categorica[i]
        fig.add_scatter(x=s["Date"], y=s["movil"], mode="lines", line=dict(color=color, width=2),
                        name=nombre_ciudad(c),
                        hovertemplate=f"{nombre_ciudad(c)}: <b>%{{y:.1f}}</b> µg/m³<extra></extra>")
        if not s.empty:
            fig.add_annotation(x=s["Date"].iloc[-1], y=s["movil"].iloc[-1], text=nombre_ciudad(c),
                               xanchor="left", xshift=6, showarrow=False,
                               font=dict(size=11, color=t.tinta))
        if episodios is not None and not episodios.empty:
            e = episodios[episodios["City"] == c]
            if not e.empty:
                tope = max(tope, float(e["valor"].max()) * 1.05)
            fig.add_scatter(x=e["Date"], y=e["valor"], mode="markers",
                            marker=dict(size=9, color=color, symbol="diamond",
                                        line=dict(color=t.superficie, width=1.5)),
                            name=f"Episodios · {nombre_ciudad(c)}",
                            customdata=np.stack([e["veces_mediana"]], axis=-1),
                            hovertemplate=(f"Episodio en {nombre_ciudad(c)}: <b>%{{y:.1f}}</b> µg/m³ "
                                           "(%{customdata[0]:.1f}× su mediana)<extra></extra>"))
    _lineas_referencia(fig, contaminante, t)
    fig.update_layout(
        hovermode="x unified", showlegend=False,
        xaxis=dict(range=[movil["Date"].min(), movil["Date"].max()] if not movil.empty else None,
                   showspikes=True, spikemode="across", spikethickness=1, spikecolor=t.eje,
                   spikedash="solid", **_eje_meses(movil["Date"])),
        yaxis=dict(range=[0, tope], showgrid=True, title=dict(text=f"{contaminante} · µg/m³")),
        margin=dict(l=8, r=96, t=12, b=8),
    )
    return _base(fig, t, alto)


def barras_mes(mes, contaminante, t: Tema, alto=380):
    """% de días sobre la guía por mes. Eje completo (0–100 %); etiquetas solo en los extremos."""
    fig = go.Figure(go.Bar(
        x=mes["nombre"], y=mes["pct_sobre_guia"],
        marker=dict(color=t.severidad[3], line=dict(color=t.superficie, width=1), cornerradius=4),
        customdata=np.stack([mes["n"], mes["mediana"]], axis=-1),
        hovertemplate=("<b>%{x}</b><br>%{y:.1f} % de los días sobre la guía<br>"
                       f"Mediana {contaminante}: %{{customdata[1]:.1f}} µg/m³ · %{{customdata[0]}} días"
                       "<extra></extra>"),
    ))
    if not mes.empty:
        for fila in (mes.loc[mes["pct_sobre_guia"].idxmin()], mes.loc[mes["pct_sobre_guia"].idxmax()]):
            fig.add_annotation(x=fila["nombre"], y=fila["pct_sobre_guia"], yshift=10, showarrow=False,
                               text=f"{fila['pct_sobre_guia']:.0f} %", font=dict(size=11, color=t.tinta))
    fig.update_layout(
        bargap=0.25,
        yaxis=dict(range=[0, 108], tickvals=[0, 25, 50, 75, 100],
                   ticktext=["0 %", "25 %", "50 %", "75 %", "100 %"], showgrid=True),
        xaxis=dict(tickfont=dict(size=11, color=t.tenue)),
        margin=dict(l=8, r=8, t=12, b=8),
    )
    return _base(fig, t, alto)


def dispersion_sensor(df, t: Tema, alto=420):
    """PM10 vs PM2.5. Por encima de la diagonal y = x está la zona físicamente imposible."""
    imposible = df["PM2.5"] > df["PM10"]
    tope = max(200.0, float(df["PM10"].max()), float(df["PM2.5"].max()))
    fig = go.Figure()
    fig.add_scatter(x=[0, tope, 0, 0], y=[0, tope, tope, 0], fill="toself", mode="lines",
                    line=dict(width=0), fillcolor=_rgba(t.critico, 0.07), hoverinfo="skip",
                    showlegend=False)
    for mascara, color, nombre, opacidad in [(~imposible, t.tenue, "Lectura coherente", 0.4),
                                             (imposible, t.critico, "Lectura imposible", 0.6)]:
        d = df[mascara]
        fig.add_scattergl(
            x=d["PM10"], y=d["PM2.5"], mode="markers", name=nombre,
            marker=dict(size=4, color=color, opacity=opacidad),
            customdata=np.stack([d["City"].astype(str).map(nombre_ciudad),
                                 d["Date"].dt.strftime("%d/%m/%Y"), d["PM2.5"] / d["PM10"]], axis=-1),
            hovertemplate=(f"<b>{nombre}</b><br>%{{customdata[0]}} · %{{customdata[1]}}<br>"
                           "PM10 %{x:.1f} · PM2.5 %{y:.1f} µg/m³<br>"
                           "PM2.5 / PM10 = %{customdata[2]:.2f}<extra></extra>"))
    fig.add_scatter(x=[0, tope], y=[0, tope], mode="lines", hoverinfo="skip", showlegend=False,
                    line=dict(color=t.tinta_2, width=1.2, dash="dash"))
    fig.add_annotation(x=tope * 0.05, y=tope * 0.74, xanchor="left", showarrow=False, align="left",
                       text="<b>⚠ Zona imposible</b><br>PM2.5 &gt; PM10", font=dict(size=12, color=t.critico),
                       bgcolor=_rgba(t.superficie, 0.92), borderpad=6)
    fig.add_annotation(x=tope * 0.78, y=tope * 0.78, xanchor="left", yanchor="top", showarrow=False,
                       text="y = x", font=dict(size=11, color=t.tinta_2), yshift=-4, xshift=6,
                       bgcolor=_rgba(t.superficie, 0.92), borderpad=3)
    fig.update_layout(
        showlegend=False,
        xaxis=dict(range=[0, tope], title=dict(text="PM10 · µg/m³"), showgrid=True),
        yaxis=dict(range=[0, tope * 0.8], title=dict(text="PM2.5 · µg/m³"), showgrid=True),
        margin=dict(l=8, r=8, t=8, b=8),
    )
    return _base(fig, t, alto)


def _rgba(hex_color, alfa):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alfa})"


# ============================== Capítulo 03 ==============================

ICONO_VEREDICTO = {"Descartada": "✕", "Confirmada": "✓", "Real pero menor": "≈", "No aplica": "–"}


def _bonito(grupo):
    return nombre_ciudad(grupo) if str(grupo).islower() else str(grupo)


def efectos(ev, t: Tema, alto=None):
    """Tamaño del efecto por factor sobre una franja de 'efecto despreciable'."""
    ev = ev.iloc[::-1].reset_index(drop=True)          # el primer factor queda arriba
    aplicables = ev[ev["veredicto"] != "No aplica"]
    umbral = float(ev["umbral"].iloc[0]) if not ev.empty else 0.0
    tope = max(umbral * 2.5, float(aplicables["efecto"].max()) * 1.15 if not aplicables.empty else 0, 1)
    colores = {"Confirmada": t.acento, "Real pero menor": t.tinta_2, "Descartada": t.tenue}
    fig = go.Figure()
    fig.add_vrect(x0=0, x1=umbral, fillcolor=t.grilla, opacity=1, line_width=0, layer="below")
    fig.add_annotation(x=umbral / 2, y=1, yref="paper", yanchor="bottom", showarrow=False,
                       text="efecto despreciable", font=dict(size=11, color=t.tenue))
    fig.add_annotation(x=umbral, y=1, yref="paper", yanchor="bottom", xanchor="left", xshift=4,
                       showarrow=False, text=f"umbral de relevancia {umbral:.1f} µg/m³",
                       font=dict(size=11, color=t.tinta_2))
    for _, f in aplicables.iterrows():
        fig.add_shape(type="line", x0=0, x1=f["efecto"], y0=f["factor"], y1=f["factor"],
                      line=dict(color=t.eje, width=2), layer="below")
    # categorías explícitas para conservar las filas "No aplica"
    fig.add_scatter(x=[None] * len(ev), y=ev["factor"], mode="markers", hoverinfo="skip",
                    showlegend=False)
    if not aplicables.empty:
        fig.add_scatter(
            x=aplicables["efecto"], y=aplicables["factor"], mode="markers",
            marker=dict(size=15, color=[colores[v] for v in aplicables["veredicto"]],
                        line=dict(color=t.superficie, width=2)),
            customdata=np.stack([aplicables["prueba"], aplicables["estadistico"], aplicables["p"],
                                 aplicables["efecto_rel"], aplicables["grupo_min"].map(_bonito),
                                 aplicables["grupo_max"].map(_bonito), aplicables["veredicto"]], axis=-1),
            hovertemplate=("<b>%{y}</b> · %{customdata[6]}<br>"
                           "Diferencia entre medianas: <b>%{x:.1f} µg/m³</b> "
                           "(%{customdata[3]:.1f} % de la mediana)<br>"
                           "Menos contaminado: %{customdata[4]}<br>Más contaminado: %{customdata[5]}<br>"
                           "%{customdata[0]}: %{customdata[1]}, p = %{customdata[2]:.3f}<extra></extra>"))
    for _, f in ev.iterrows():
        icono = ICONO_VEREDICTO[f["veredicto"]]
        detalle = f"p = {f['p']:.2f}" if f["veredicto"] != "No aplica" else "un solo grupo"
        fig.add_annotation(x=1, xref="paper", xanchor="left", xshift=16, y=f["factor"], showarrow=False,
                           align="left", text=(f"<b>{icono} {f['veredicto']}</b>  "
                                               f"<span style='color:{t.tenue}'>{detalle}</span>"),
                           font=dict(size=12.5, color=t.tinta if f["veredicto"] == "Confirmada" else t.tinta_2))
    fig.update_layout(
        showlegend=False,
        xaxis=dict(range=[0, tope], showgrid=True,
                   title=dict(text="Diferencia entre la mediana del grupo más y el menos contaminado (µg/m³)")),
        yaxis=dict(tickfont=dict(size=13, color=t.tinta)),
        margin=dict(l=8, r=220, t=30, b=8),
    )
    return _base(fig, t, alto or 58 * len(ev) + 110)


def grupos(tablas, contaminante, t: Tema, alto=380):
    """Pequeños múltiplos: mediana (punto) e IQR (bigote) por grupo. Eje Y desde 0 en todos."""
    from plotly.subplots import make_subplots
    nombres = list(tablas)
    fig = make_subplots(rows=1, cols=len(nombres), shared_yaxes=True, horizontal_spacing=0.035,
                        subplot_titles=nombres)
    tope = niveles(contaminante)[-1].desde * 2
    for i, nombre in enumerate(nombres, start=1):
        g = tablas[nombre]
        etiquetas = [_bonito(x).replace(" · ", "<br>") for x in g["grupo"]]
        fig.add_scatter(
            x=etiquetas, y=g["mediana"], mode="markers", row=1, col=i,
            marker=dict(size=10, color=t.acento, line=dict(color=t.superficie, width=2)),
            error_y=dict(type="data", symmetric=False, array=g["p75"] - g["mediana"],
                         arrayminus=g["mediana"] - g["p25"], color=t.eje, thickness=2, width=0),
            customdata=np.stack([g["p25"], g["p75"], g["n"]], axis=-1),
            hovertemplate=("<b>%{x}</b><br>Mediana: <b>%{y:.1f} µg/m³</b><br>"
                           "Rango intercuartil: %{customdata[0]:.1f}–%{customdata[1]:.1f}<br>"
                           "%{customdata[2]} días<extra></extra>"))
        fig.add_hline(y=guia(contaminante), row=1, col=i, line=dict(color=t.tinta_2, width=1, dash="dash"))
    fig.update_yaxes(range=[0, tope], showgrid=True, gridcolor=t.grilla, zeroline=False,
                     tickfont=dict(color=t.tenue, size=11))
    fig.update_yaxes(title=dict(text=f"{contaminante} · µg/m³", font=dict(size=12, color=t.tinta_2)),
                     row=1, col=1)
    fig.update_xaxes(tickfont=dict(size=10.5, color=t.tinta_2), showgrid=False, tickangle=0)
    fig.update_annotations(font=dict(size=13, color=t.tinta))
    fig.update_layout(showlegend=False, margin=dict(l=8, r=8, t=36, b=56))
    return _base(fig, t, alto)


def dumbbell_finde(d, contaminante, t: Tema):
    """Mediana laborable vs. fin de semana por ciudad. Eje desde 0 para no exagerar diferencias."""
    ciudades = [nombre_ciudad(c) for c in d["City"]]
    tope = niveles(contaminante)[-1].desde * 2
    fig = go.Figure()
    for _, f in d.iterrows():
        fig.add_shape(type="line", x0=f["laborable"], x1=f["fin_semana"], y0=nombre_ciudad(f["City"]),
                      y1=nombre_ciudad(f["City"]), line=dict(color=t.eje, width=3), layer="below")
    comunes = np.stack([d["laborable"], d["fin_semana"], d["diferencia"], d["p"]], axis=-1)
    plantilla = ("<b>%{y}</b><br>Laborable %{customdata[0]:.1f} · Fin de semana %{customdata[1]:.1f} µg/m³<br>"
                 "Diferencia %{customdata[2]:+.1f} µg/m³ · Mann-Whitney p = %{customdata[3]:.2f}"
                 "<extra></extra>")
    fig.add_scatter(x=d["laborable"], y=ciudades, mode="markers", name="Laborable",
                    marker=dict(size=10, color=t.tenue, line=dict(color=t.superficie, width=2)),
                    customdata=comunes, hovertemplate=plantilla)
    fig.add_scatter(x=d["fin_semana"], y=ciudades, mode="markers", name="Fin de semana",
                    marker=dict(size=10, color=t.acento, line=dict(color=t.superficie, width=2)),
                    customdata=comunes, hovertemplate=plantilla)
    fig.add_vline(x=guia(contaminante), line=dict(color=t.tinta_2, width=1, dash="dash"),
                  annotation=dict(text=f"Guía {guia(contaminante):g}", font=dict(size=11, color=t.tinta_2)),
                  annotation_position="bottom right")
    fig.update_layout(
        showlegend=True, legend=dict(orientation="h", x=1, xanchor="right", y=1.0, yanchor="bottom"),
        xaxis=dict(range=[0, tope], showgrid=True, title=dict(text=f"Mediana de {contaminante} · µg/m³")),
        yaxis=dict(tickfont=dict(size=12, color=t.tinta_2)),
        margin=dict(l=8, r=8, t=40, b=8),
    )
    return _base(fig, t, 24 * len(d) + 120)


def grupos_horizontal(g, contaminante, t: Tema, mediana_global=None):
    """Mediana e IQR por grupo en filas (para muchas categorías, p. ej. 20 ciudades)."""
    etiquetas = [_bonito(x) for x in g["grupo"]]
    tope = niveles(contaminante)[-1].desde * 2
    fig = go.Figure(go.Scatter(
        x=g["mediana"], y=etiquetas, mode="markers",
        marker=dict(size=10, color=t.acento, line=dict(color=t.superficie, width=2)),
        error_x=dict(type="data", symmetric=False, array=g["p75"] - g["mediana"],
                     arrayminus=g["mediana"] - g["p25"], color=t.eje, thickness=2, width=0),
        customdata=np.stack([g["p25"], g["p75"], g["n"]], axis=-1),
        hovertemplate=("<b>%{y}</b><br>Mediana: <b>%{x:.1f} µg/m³</b><br>"
                       "Rango intercuartil: %{customdata[0]:.1f}–%{customdata[1]:.1f}<br>"
                       "%{customdata[2]} días<extra></extra>")))
    fig.add_vline(x=guia(contaminante), line=dict(color=t.tinta_2, width=1, dash="dash"),
                  annotation=dict(text=f"Guía {guia(contaminante):g}", font=dict(size=11, color=t.tinta_2)),
                  annotation_position="top")
    if mediana_global is not None:
        fig.add_vline(x=mediana_global, line=dict(color=t.acento, width=1),
                      annotation=dict(text=f"Mediana global {mediana_global:.0f}",
                                      font=dict(size=11, color=t.acento)),
                      annotation_position="bottom right")
    fig.update_layout(
        xaxis=dict(range=[0, tope], showgrid=True, title=dict(text=f"{contaminante} · µg/m³")),
        yaxis=dict(tickfont=dict(size=12, color=t.tinta_2)),
        margin=dict(l=8, r=8, t=30, b=8), showlegend=False,
    )
    return _base(fig, t, 24 * len(g) + 110)


# ============================== Capítulo 04 ==============================

def _etiqueta_meta(meta, valor):
    return f"{'Guía OMS' if meta == 'guía' else meta} · {valor:g} µg/m³"


def antes_despues(sim, contaminante, t: Tema, reduccion, alto=200):
    """Dos barras al 100 % (hoy y escenario simulado) con los días en cada nivel OMS."""
    filas = ["Hoy", f"Con −{reduccion:g} %"]
    nv = {n.nombre: n for n in niveles(contaminante)}
    fig = go.Figure()
    for _, s in sim.iterrows():
        valores = [s["pct_actual"], s["pct_simulado"]]
        fig.add_bar(
            y=filas, x=valores, orientation="h", name=s["nivel"],
            marker=dict(color=t.severidad[s["indice"]], line=dict(color=t.superficie, width=1)),
            text=[f"{v:.0f} %" if v >= 7 else "" for v in valores], textposition="inside",
            insidetextanchor="middle", textfont=dict(color=t.texto_sobre[s["indice"]], size=12),
            customdata=[nv[s["nivel"]].rango] * 2,
            hovertemplate=(f"<b>%{{y}}</b><br>{s['nivel']} ({contaminante} %{{customdata}} µg/m³)<br>"
                           "<b>%{x:.1f} %</b> de los días<extra></extra>"))
    fig.update_layout(
        barmode="stack", bargap=0.35, showlegend=False,
        xaxis=dict(range=[0, 100], showgrid=True, tickvals=[0, 25, 50, 75, 100],
                   ticktext=["0 %", "25 %", "50 %", "75 %", "100 %"]),
        yaxis=dict(autorange="reversed", tickfont=dict(size=13, color=t.tinta)),
        margin=dict(l=8, r=8, t=8, b=8))
    return _base(fig, t, alto)


def hoja_ruta(req, contaminante, t: Tema, reduccion, alto=None):
    """Recorte necesario para alcanzar cada meta OMS. Las metas que el escenario alcanza se resaltan."""
    etiquetas = [_etiqueta_meta(m, v) for m, v in zip(req["meta"], req["valor"])]
    alcanzada = req["reduccion"] <= reduccion + 1e-9
    fig = go.Figure(go.Bar(
        y=etiquetas, x=req["reduccion"], orientation="h",
        marker=dict(color=[t.acento if a else t.contexto for a in alcanzada]),
        customdata=np.stack([req["valor"], ["alcanzada" if a else "fuera de alcance" for a in alcanzada]],
                            axis=-1),
        hovertemplate=("<b>%{y}</b><br>Recorte necesario: <b>%{x:.0f} %</b><br>"
                       "Con el escenario elegido: %{customdata[1]}<extra></extra>")))
    for e, r, a in zip(etiquetas, req["reduccion"], alcanzada):
        fig.add_annotation(x=r, y=e, xanchor="left", xshift=6, showarrow=False,
                           text=f"<b>−{r:.0f} %</b>" if a else f"−{r:.0f} %",
                           font=dict(size=12.5, color=t.tinta if a else t.tinta_2))
    fig.add_vline(x=reduccion, line=dict(color=t.tinta, width=1.5, dash="dot"),
                  annotation=dict(text=f"Escenario −{reduccion:g} %", font=dict(size=11, color=t.tinta)),
                  annotation_position="top")
    fig.update_layout(
        showlegend=False, bargap=0.38,
        xaxis=dict(range=[0, 105], showgrid=True, tickvals=[0, 25, 50, 75, 100],
                   ticktext=["0 %", "25 %", "50 %", "75 %", "100 %"],
                   title=dict(text="Recorte de las concentraciones de fondo")),
        yaxis=dict(autorange="reversed", tickfont=dict(size=12.5, color=t.tinta_2)),
        margin=dict(l=8, r=8, t=30, b=8))
    return _base(fig, t, alto or 52 * len(req) + 100)


def ranking_ciudades(pri, t: Tema, seleccion=(), alto=None):
    """% de días críticos por ciudad (las tres guías superadas a la vez), de mayor a menor."""
    sel = set(seleccion)
    pri = pri.iloc[::-1]                         # la más crítica arriba
    nombres = [nombre_ciudad(c) for c in pri["City"]]
    opacidad = [1 if not sel or c in sel else 0.28 for c in pri["City"]]
    fig = go.Figure(go.Bar(
        y=nombres, x=pri["pct_criticos"], orientation="h",
        marker=dict(color=t.severidad[4], opacity=opacidad),
        customdata=np.stack([pri["dias_criticos"], pri["n"], pri["pct_sobre_it1"], pri["City"]], axis=-1),
        hovertemplate=("<b>%{y}</b><br>Días críticos: <b>%{x:.1f} %</b> "
                       "(%{customdata[0]} de %{customdata[1]})<br>"
                       "Sobre IT-1: %{customdata[2]:.1f} %<extra></extra>")))
    for n, v in zip(nombres, pri["pct_criticos"]):
        fig.add_annotation(x=v, y=n, xanchor="left", xshift=6, showarrow=False, text=f"{v:.0f} %",
                           font=dict(size=12, color=t.tinta_2))
    tope = max(float(pri["pct_criticos"].max()) * 1.15, 10) if not pri.empty else 100
    fig.update_layout(
        showlegend=False, bargap=0.3, clickmode="event+select",
        xaxis=dict(range=[0, tope], showgrid=True, ticksuffix=" %", side="top"),
        yaxis=dict(tickfont=dict(size=12.5, color=t.tinta_2)),
        margin=dict(l=8, r=8, t=24, b=4))
    return _base(fig, t, alto or max(220, 24 * len(pri) + 50))


# ============================== Auditoría del dato ==============================

def embudo(emb, t: Tema, alto=None):
    """Filas que quedan en cada etapa de la limpieza; la última (el procesado) en el acento."""
    emb = emb.reset_index(drop=True)
    total = float(emb["filas"].iloc[0])
    ultima = len(emb) - 1
    colores = [t.acento if i == ultima else t.contexto for i in range(len(emb))]
    fig = go.Figure(go.Bar(
        y=emb["etapa"], x=emb["filas"], orientation="h", marker=dict(color=colores),
        customdata=(emb["filas"] / total * 100), hovertemplate=(
            "<b>%{y}</b><br>%{x:,} filas (%{customdata:.1f} % del crudo)<extra></extra>")))
    for i, f in emb.iterrows():
        quitadas = "" if i == 0 else f"  −{int(emb['filas'].iloc[i - 1] - f['filas']):,}"
        fig.add_annotation(x=f["filas"], y=f["etapa"], xanchor="left", xshift=6, showarrow=False,
                           text=f"<b>{int(f['filas']):,}</b><span style='color:{t.tenue}'>{quitadas}</span>",
                           font=dict(size=12.5, color=t.tinta if i == ultima else t.tinta_2))
    fig.update_layout(
        showlegend=False, bargap=0.35,
        xaxis=dict(range=[0, total * 1.25], showgrid=True, tickformat=",d"),
        yaxis=dict(autorange="reversed", tickfont=dict(size=12.5, color=t.tinta_2)),
        margin=dict(l=8, r=8, t=8, b=8))
    return _base(fig, t, alto or 60 * len(emb) + 60)


NOMBRES_VARIABLE = {"Temperature": "Temperatura", "Humidity": "Humedad", "Wind Speed": "Viento"}


def deltas_distribucion(dist, t: Tema, banda=1.0, alto=None):
    """Cambio % de la media (●) y de la desviación (◆) de cada variable tras el pipeline.

    Eje simétrico centrado en 0 (un cambio puede ser negativo); la franja gris marca ±`banda` %.
    """
    d = dist.iloc[::-1].reset_index(drop=True)
    nombres = [NOMBRES_VARIABLE.get(v, v) for v in d["variable"]]
    tope = max(3.0, float(np.ceil(d[["delta_media_pct", "delta_std_pct"]].abs().to_numpy().max() * 1.3)))
    fig = go.Figure()
    fig.add_vrect(x0=-banda, x1=banda, fillcolor=t.grilla, opacity=1, line_width=0, layer="below")
    fig.add_vline(x=0, line=dict(color=t.eje, width=1))
    for col, nombre, simbolo, color in [("delta_media_pct", "Media", "circle", t.acento),
                                        ("delta_std_pct", "Desviación", "diamond", t.tinta_2)]:
        fig.add_scatter(
            x=d[col], y=nombres, mode="markers", name=nombre,
            marker=dict(symbol=simbolo, size=11, color=color, line=dict(color=t.superficie, width=1.5)),
            customdata=np.stack([d["ks_p"]], axis=-1),
            hovertemplate=(f"<b>%{{y}}</b><br>{nombre}: <b>%{{x:+.2f}} %</b><br>"
                           "KS p = %{customdata[0]:.2f}<extra></extra>"))
    for n, (_, f) in zip(nombres, d.iterrows()):
        marca = "✓" if f["intacta"] else "✕"
        fig.add_annotation(x=1, xref="paper", xanchor="left", xshift=14, y=n, showarrow=False,
                           text=f"{marca} KS p = {f['ks_p']:.2f}",
                           font=dict(size=12, color=t.tinta_2 if f["intacta"] else t.critico))
    fig.add_annotation(x=0, y=1, yref="paper", yanchor="bottom", showarrow=False,
                       text=f"cambio despreciable (±{banda:g} %)", font=dict(size=11, color=t.tenue))
    fig.update_layout(
        legend=dict(orientation="h", y=-0.12, yanchor="top", x=0, bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(range=[-tope, tope], showgrid=True, ticksuffix=" %", zeroline=False,
                   title=dict(text="Cambio respecto del CSV crudo")),
        yaxis=dict(tickfont=dict(size=12.5, color=t.tinta)),
        margin=dict(l=8, r=130, t=28, b=8))
    return _base(fig, t, alto or 36 * len(d) + 150)

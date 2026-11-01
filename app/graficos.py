"""Constructores de figuras Plotly. Reciben datos ya agregados y un `Tema`; no leen estado de UI."""

import numpy as np
import plotly.graph_objects as go

from air_quality.metricas import nombre_ciudad
from air_quality.severidad import guia, niveles

from tema import FUENTE, Tema, escala_secuencial

CONFIG = {"displayModeBar": False, "responsive": True, "scrollZoom": False}


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

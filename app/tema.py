"""Sistema visual del dashboard: tokens de color, plantilla Plotly y CSS.

Paletas validadas con el validador de la skill dataviz (OKLab, simulación CVD):
- `severidad`: rampa ordinal de un solo tono (h≈38°), 6 pasos, ΔL ≥ 0.06 entre pasos y el
  extremo claro ≥ 2:1 contra la superficie, validada por separado en claro y en oscuro.
  En oscuro el ancla se invierte: lo leve es oscuro (se funde con el fondo) y lo severo brilla.
- `secuencial`: la misma familia de tono, continua, para concentraciones (mapa, calendario).
- `acento`: azul, único color de énfasis y selección. No compite con la rampa cálida.
- `categorica`: primeros 3 slots de la paleta documentada de la skill (validados en todos los
  pares, para líneas y dispersión). Solo cuando se comparan ciudades seleccionadas.
"""

from dataclasses import dataclass

import plotly.graph_objects as go
import plotly.io as pio

FUENTE = "Inter, system-ui, -apple-system, 'Segoe UI', sans-serif"


@dataclass(frozen=True)
class Tema:
    nombre: str
    pagina: str
    superficie: str
    tinta: str
    tinta_2: str
    tenue: str
    grilla: str
    eje: str
    borde: str
    acento: str
    contexto: str          # gris de de-énfasis (marcas no seleccionadas)
    tierra: str
    agua: str
    severidad: tuple       # índice 0..5 de air_quality.severidad
    secuencial: tuple      # bajo → alto
    texto_sobre: tuple     # color de etiqueta legible sobre cada paso de severidad
    categorica: tuple      # hasta 3 ciudades a la vez (slots 1-3 validados en todos los pares)
    critico: str = "#d03b3b"   # estado: lectura inválida (siempre con ícono + etiqueta)


CLARO = Tema(
    nombre="claro",
    pagina="#f4f3ef", superficie="#fcfcfb",
    tinta="#0b0b0b", tinta_2="#52514e", tenue="#898781",
    grilla="#e8e7e1", eje="#c3c2b7", borde="rgba(11,11,11,0.10)",
    acento="#2a78d6", contexto="#d4d3cc",
    tierra="#ebeae4", agua="#fcfcfb",
    severidad=("#ed987d", "#e37958", "#d65a32", "#bf4213", "#a23102", "#832600"),
    secuencial=("#ffeee8", "#fecab9", "#f99b7e", "#e4673f", "#bc3e0d", "#902a00", "#691d00"),
    texto_sobre=("#0b0b0b", "#0b0b0b", "#ffffff", "#ffffff", "#ffffff", "#ffffff"),
    categorica=("#2a78d6", "#eb6834", "#1baf7a"),
)

OSCURO = Tema(
    nombre="oscuro",
    pagina="#0d0d0d", superficie="#1a1a19",
    tinta="#f0efec", tinta_2="#c3c2b7", tenue="#898781",
    grilla="#2c2c2a", eje="#383835", borde="rgba(255,255,255,0.10)",
    acento="#3987e5", contexto="#3a3a37",
    tierra="#262624", agua="#1a1a19",
    severidad=("#8b381d", "#ab4321", "#c9532c", "#e4673f", "#f48462", "#fea387"),
    secuencial=("#281c18", "#532719", "#843217", "#bc461e", "#e76a43", "#fe9979", "#fecab9"),
    texto_sobre=("#ffffff", "#ffffff", "#ffffff", "#0b0b0b", "#0b0b0b", "#0b0b0b"),
    categorica=("#3987e5", "#d95926", "#199e70"),
)


def tema(oscuro: bool) -> Tema:
    return OSCURO if oscuro else CLARO


def escala_secuencial(t: Tema):
    n = len(t.secuencial) - 1
    return [[i / n, c] for i, c in enumerate(t.secuencial)]


def plantilla(t: Tema) -> go.layout.Template:
    """Plantilla Plotly: tinta recesiva, grilla de una línea, sin bordes ni chartjunk."""
    eje = dict(showgrid=False, zeroline=False, showline=False, ticks="",
               tickfont=dict(color=t.tenue, size=12), title=dict(font=dict(color=t.tinta_2, size=12)),
               linecolor=t.eje, gridcolor=t.grilla, gridwidth=1, automargin=True)
    return go.layout.Template(layout=go.Layout(
        font=dict(family=FUENTE, color=t.tinta_2, size=13),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        colorway=[t.acento],
        margin=dict(l=8, r=8, t=8, b=8),
        xaxis=eje, yaxis=eje,
        hoverlabel=dict(bgcolor=t.superficie, bordercolor=t.eje,
                        font=dict(family=FUENTE, color=t.tinta, size=13), align="left"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text="",
                    font=dict(color=t.tinta_2, size=12), itemclick=False, itemdoubleclick=False),
        hovermode="closest", dragmode=False,
        coloraxis=dict(colorbar=dict(outlinewidth=0, thickness=10, len=0.6,
                                     tickfont=dict(color=t.tenue, size=11))),
    ))


def logo_svg(t: Tema, con_texto=True) -> str:
    """Logo del tablero: el punto de severidad de la marca y tres trazos de viento.

    Se genera desde el tema para que los colores sigan a la paleta en claro y en oscuro.
    """
    trazos = (f'<circle cx="7" cy="16" r="4.5" fill="{t.severidad[5]}"/>'
              f'<g fill="none" stroke="{t.tinta}" stroke-width="2.4" stroke-linecap="round">'
              '<path d="M14 11.5h9a3.5 3.5 0 1 0-3.5-3.5"/>'
              '<path d="M14 16h6"/>'
              '<path d="M14 20.5h12a3.5 3.5 0 1 1-3.5 3.5"/></g>')
    if not con_texto:
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">{trazos}</svg>'
    # en mayúsculas con tracking amplio, como la marca de la cabecera
    texto = (f'<text x="38" y="21" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif" '
             f'font-size="13" font-weight="700" letter-spacing="1.3" fill="{t.tinta}">CALIDAD DEL AIRE</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 214 32">{trazos}{texto}</svg>'


def registrar_plantillas():
    for t in (CLARO, OSCURO):
        pio.templates[f"aire_{t.nombre}"] = plantilla(t)


def css(t: Tema) -> str:
    """CSS global. Los tokens se exponen como variables para los componentes HTML."""
    oscuro = t is OSCURO
    base = f"""
:root {{
  --pagina:{t.pagina}; --superficie:{t.superficie}; --tinta:{t.tinta}; --tinta-2:{t.tinta_2};
  --tenue:{t.tenue}; --grilla:{t.grilla}; --eje:{t.eje}; --borde:{t.borde}; --acento:{t.acento};
  --sev-0:{t.severidad[0]}; --sev-1:{t.severidad[1]}; --sev-2:{t.severidad[2]};
  --sev-3:{t.severidad[3]}; --sev-4:{t.severidad[4]}; --sev-5:{t.severidad[5]};
  --fuente:{FUENTE};
}}
.stApp {{ background: var(--pagina); color: var(--tinta); }}
[data-testid="stHeader"] {{ background: transparent; }}
/* Del toolbar de Streamlit solo se conserva el botón para expandir la barra lateral, el logo y el
   indicador de carga. El toolbar ocupa todo el ancho y es transparente: no debe tapar los clics. */
[data-testid="stDecoration"], [data-testid="stMainMenu"], [data-testid="stAppDeployButton"],
[data-testid="stToolbarActions"] {{ display: none; }}
[data-testid="stToolbar"] {{ pointer-events: none; }}
[data-testid="stToolbar"] button, [data-testid="stToolbar"] a, [data-testid="stStatusWidget"] {{ pointer-events: auto; }}
.block-container {{ max-width: 1440px; padding: 1.6rem 2.5rem 4rem; }}
[data-testid="stPlotlyChart"] {{ background: transparent; }}
h1, h2, h3, h4, p, span, label, li {{ font-family: var(--fuente); }}

/* Tarjetas: contenedores con key="tarjeta-..." */
[class*="st-key-tarjeta"] {{
  background: var(--superficie); border: 1px solid var(--borde); border-radius: 16px;
  padding: 1.25rem 1.4rem 1rem;
}}
/* Barra lateral de filtros */
[data-testid="stSidebar"] {{ background: var(--superficie); border-right: 1px solid var(--borde); }}
[data-testid="stSidebar"] label p {{ font-size: .72rem; letter-spacing: .06em; text-transform: uppercase;
  color: var(--tenue); font-weight: 600; }}
[data-testid="stSidebarUserContent"] {{ padding-top: .5rem; }}
.lateral-titulo {{ font-size:.78rem; letter-spacing:.14em; text-transform:uppercase; color:var(--tinta);
  font-weight:700; }}
.lateral-sub {{ font-size:.82rem; color:var(--tinta-2); margin:.2rem 0 .2rem; }}
.lateral-pie {{ font-size:.76rem; color:var(--tenue); line-height:1.6; border-top:1px solid var(--grilla);
  padding-top:.8rem; margin-top:.4rem; }}
.lateral-pie a, .cab .meta a {{ color: var(--acento); text-decoration:none; }}
.lateral-pie a:hover, .cab .meta a:hover {{ text-decoration:underline; }}

/* Marca + botón de tema */
.marca {{ font-size:.78rem; letter-spacing:.14em; text-transform:uppercase; color:var(--tenue);
  font-weight:600; display:flex; align-items:center; gap:.5rem; }}
.marca .punto {{ width:.55rem; height:.55rem; border-radius:50%; background:var(--sev-5); }}
.st-key-btn_tema {{ display:flex; justify-content:flex-end; }}
.st-key-btn_tema button {{ border-radius:999px; padding:.3rem; min-height:2.2rem; min-width:2.2rem;
  color: var(--tinta-2) !important; }}
.st-key-btn_tema button:hover {{ color: var(--acento) !important; background: var(--grilla) !important; }}
.st-key-btn_tema button [data-testid="stMarkdownContainer"] {{ position:absolute; width:1px; height:1px;
  overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; }}
.st-key-btn_tema button span[data-testid="stIconMaterial"] {{ font-size:1.35rem; }}

/* Menú de capítulos (st.page_link con estilo de píldora) */
.st-key-nav-cap {{ margin: 1.1rem 0 .2rem; flex-wrap: wrap; }}
[class*="st-key-nav-"] [data-testid="stPageLink"] a {{ border:1px solid var(--borde); border-radius:999px;
  background: var(--superficie); padding:.3rem .95rem; margin:0; }}
[class*="st-key-nav-"] [data-testid="stPageLink"] a span, [class*="st-key-nav-"] [data-testid="stPageLink"] a p {{
  font-size:.82rem; color: var(--tinta-2); font-variant-numeric: tabular-nums; white-space: pre; }}
[class*="st-key-nav-item"] [data-testid="stPageLink"] a:hover {{ border-color: var(--acento); }}
[class*="st-key-nav-activo"] [data-testid="stPageLink"] a {{ background: var(--tinta); border-color: var(--tinta); }}
[class*="st-key-nav-activo"] [data-testid="stPageLink"] a span,
[class*="st-key-nav-activo"] [data-testid="stPageLink"] a p {{ color: var(--superficie); font-weight:600; }}

/* El anexo va aparte, a la derecha del menú, con menos peso visual */
/* Streamlit envuelve cada contenedor en un div: el elemento flex es ese envoltorio */
.st-key-nav-cap > div:has(> [class*="st-key-nav-anexo"]) {{ margin-left: auto; }}
[class*="st-key-nav-anexo-item"] [data-testid="stPageLink"] a {{ border-style: dashed; background: transparent; }}
[data-testid="stSidebar"] [data-testid="stPageLink"] a span, [data-testid="stSidebar"] [data-testid="stPageLink"] a p {{
  font-size:.8rem; color: var(--acento); }}

/* Controles de calidad (auditoría) */
.verificaciones {{ list-style:none; margin:.3rem 0 0; padding:0; display:grid; gap:.15rem; }}
.verificaciones li {{ display:grid; grid-template-columns: 1.8rem 1fr; gap:.4rem; padding:.6rem 0;
  border-bottom:1px solid var(--grilla); }}
.verificaciones li:last-child {{ border-bottom:none; }}
.verificaciones .icono {{ font-size:1rem; font-weight:700; color:var(--tinta-2); line-height:1.4; }}
.verificaciones b {{ color:var(--tinta); font-weight:600; font-size:.92rem; }}
.verificaciones .estado {{ margin-left:.5rem; font-size:.68rem; letter-spacing:.08em; text-transform:uppercase;
  color:var(--tenue); font-weight:700; }}
.verificaciones p {{ margin:.15rem 0 0; color:var(--tinta-2); font-size:.85rem; line-height:1.45; }}
.verificaciones li.falla .icono, .verificaciones li.falla .estado {{ color:{t.critico}; }}
.verificaciones .ver-cap {{ color: var(--tenue); font-size:.78rem; }}

/* Enlace al capítulo siguiente */
.st-key-siguiente {{ margin-top: 2.6rem; padding-top: 1.2rem; border-top: 1px solid var(--grilla); }}
.st-key-siguiente [data-testid="stPageLink"] a {{ border:1px solid var(--acento); border-radius:999px;
  padding:.45rem 1.1rem; background: var(--superficie); }}
.st-key-siguiente [data-testid="stPageLink"] a span, .st-key-siguiente [data-testid="stPageLink"] a p {{
  color: var(--acento); font-weight:600; font-size:.9rem; }}
.st-key-siguiente [data-testid="stPageLink"] a:hover {{ background: color-mix(in srgb, var(--acento) 10%, var(--superficie)); }}

/* Línea "Vista: …" bajo el título del capítulo */
.activos {{ margin-top:.7rem; font-size:.82rem; color:var(--tinta-2); font-variant-numeric: tabular-nums; }}
.activos span {{ font-size:.68rem; letter-spacing:.1em; text-transform:uppercase; color:var(--tenue);
  font-weight:700; margin-right:.55rem; }}
.activos b {{ font-weight:500; }}
.activos b.on {{ color: var(--acento); font-weight:650; }}

/* ---------- Componentes HTML ---------- */
.cab {{ display:flex; justify-content:space-between; align-items:flex-end; gap:2rem;
  border-bottom: 1px solid var(--grilla); padding-bottom: 1.4rem; margin-top: .4rem; }}
.cab h1 {{ font-size: clamp(2rem, 3.4vw, 3rem); line-height:1.05; font-weight:700; letter-spacing:-.025em;
  color:var(--tinta); margin:0; padding:0; max-width: 18ch; }}
.cab .tesis {{ color:var(--tinta-2); font-size:1.05rem; line-height:1.5; max-width: 58ch; margin:.9rem 0 0; }}
.cab .meta {{ text-align:right; color:var(--tenue); font-size:.82rem; line-height:1.7; white-space:nowrap; }}
.cab .meta b {{ color:var(--tinta); font-weight:600; }}

.capitulo {{ margin: 1.8rem 0 1.4rem; display:grid; grid-template-columns: 4.2rem 1fr; gap: 0 1rem;
  scroll-margin-top: 7rem; }}
.capitulo .num {{ font-size:2.6rem; font-weight:300; color:var(--tenue); line-height:1;
  font-variant-numeric: tabular-nums; letter-spacing:-.04em; }}
.capitulo .kicker {{ font-size:.75rem; letter-spacing:.14em; text-transform:uppercase; color:var(--sev-4);
  font-weight:700; margin-bottom:.35rem; }}
.capitulo h2 {{ font-size: clamp(1.45rem, 2.3vw, 2rem); line-height:1.15; font-weight:650;
  letter-spacing:-.02em; color:var(--tinta); margin:0; padding:0; max-width: 34ch; }}
.capitulo .bajada {{ color:var(--tinta-2); font-size:1rem; line-height:1.55; margin:.6rem 0 0; max-width:70ch; }}

.hero {{ display:flex; flex-direction:column; justify-content:space-between; height:100%; min-height: 15rem; }}
.hero .rotulo, .kpi .rotulo {{ font-size:.72rem; letter-spacing:.08em; text-transform:uppercase;
  color:var(--tenue); font-weight:600; }}
.hero .cifra {{ font-size: clamp(4rem, 7.5vw, 6.4rem); font-weight:700; letter-spacing:-.05em; line-height:.95;
  color:var(--tinta); margin:.6rem 0 .4rem; }}
.hero .cifra small {{ font-size:.42em; font-weight:600; letter-spacing:-.02em; color:var(--tinta-2); margin-left:.08em; }}
.hero .texto {{ color:var(--tinta-2); font-size:1rem; line-height:1.45; max-width: 30ch; }}
.hero .texto b {{ color:var(--tinta); }}
.medidor {{ margin-top:1.2rem; }}
.medidor .pista {{ position:relative; height:10px; border-radius:999px; background:var(--grilla); overflow:hidden; }}
.medidor .relleno {{ position:absolute; inset:0 auto 0 0; border-radius:999px; background:var(--sev-4); }}
.medidor .escala {{ display:flex; justify-content:space-between; font-size:.72rem; color:var(--tenue);
  margin-top:.35rem; font-variant-numeric: tabular-nums; }}

.kpis {{ display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: .8rem; height:100%; }}
.kpi {{ background:var(--superficie); border:1px solid var(--borde); border-radius:16px; padding:1rem 1.1rem;
  display:flex; flex-direction:column; gap:.25rem; }}
.kpi .valor {{ font-size:2.1rem; font-weight:680; letter-spacing:-.035em; color:var(--tinta); line-height:1.1;
  margin-top:.35rem; }}
.kpi .valor small {{ font-size:.5em; font-weight:550; color:var(--tinta-2); margin-left:.15em; letter-spacing:0; }}
.kpi .nota {{ color:var(--tinta-2); font-size:.86rem; line-height:1.4; }}
.kpi .delta, .hero .delta {{ font-size:.78rem; color:var(--tenue); font-variant-numeric: tabular-nums; }}
.kpi .marca-sev {{ display:inline-block; width:.6rem; height:.6rem; border-radius:3px; margin-right:.4rem;
  vertical-align: baseline; }}

.titulo-graf {{ font-size:1rem; font-weight:650; color:var(--tinta); margin:0 0 .15rem; letter-spacing:-.01em; }}
.sub-graf {{ font-size:.85rem; color:var(--tinta-2); margin:0 0 .6rem; line-height:1.45; }}
.nota-graf {{ font-size:.76rem; color:var(--tenue); margin:.2rem 0 0; line-height:1.45; }}
.leyenda-sev {{ display:flex; flex-wrap:wrap; gap:.35rem 1rem; margin:.2rem 0 .7rem; }}
.leyenda-sev span {{ font-size:.78rem; color:var(--tinta-2); display:inline-flex; align-items:center; gap:.4rem; }}
.leyenda-sev i {{ width:.8rem; height:.8rem; border-radius:3px; display:inline-block; }}
.leyenda-sev em {{ color:var(--tenue); font-style:normal; font-variant-numeric: tabular-nums; }}
.vacio {{ border:1px dashed var(--eje); border-radius:16px; padding:2.4rem; text-align:center; color:var(--tinta-2); }}
.vacio b {{ color:var(--tinta); display:block; font-size:1.1rem; margin-bottom:.3rem; }}
.subseccion {{ margin: 2.2rem 0 .9rem; border-top: 1px solid var(--grilla); padding-top: 1.3rem; }}
.subseccion .kicker {{ font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; color:var(--tenue);
  font-weight:700; }}
.subseccion h3 {{ font-size:1.25rem; font-weight:650; letter-spacing:-.015em; color:var(--tinta);
  margin:.3rem 0 0; padding:0; }}
.subseccion p {{ color:var(--tinta-2); font-size:.95rem; line-height:1.5; margin:.4rem 0 0; max-width:75ch; }}
.tabla {{ width:100%; border-collapse:collapse; font-size:.88rem; font-variant-numeric: tabular-nums; }}
.tabla th {{ text-align:left; font-size:.7rem; letter-spacing:.07em; text-transform:uppercase; color:var(--tenue);
  font-weight:600; padding:.45rem .5rem; border-bottom:1px solid var(--eje); }}
.tabla td {{ padding:.5rem .5rem; border-bottom:1px solid var(--grilla); color:var(--tinta-2); }}
.tabla td b {{ color:var(--tinta); }}
.tabla .num {{ text-align:right; }}
.unidad {{ text-transform:none; letter-spacing:0; }}
.nw {{ white-space:nowrap; }}
.tabla tr:last-child td {{ border-bottom:none; }}
.tabla-scroll {{ overflow:auto; }}
.tabla-scroll thead th {{ position:sticky; top:0; background:var(--superficie); }}
.chip {{ display:inline-flex; align-items:center; gap:.4rem; font-size:.8rem; color:var(--tinta-2); }}
.chip i {{ width:.7rem; height:.7rem; border-radius:3px; display:inline-block; }}
.tarjeta-texto .rotulo {{ font-size:.72rem; letter-spacing:.08em; text-transform:uppercase; color:var(--tenue);
  font-weight:600; }}
.tarjeta-texto h4 {{ font-size:1.15rem; font-weight:650; color:var(--tinta); margin:.4rem 0 .5rem; padding:0;
  letter-spacing:-.01em; line-height:1.3; }}
.tarjeta-texto .cuerpo {{ color:var(--tinta-2); font-size:.92rem; line-height:1.55; }}
.tarjeta-texto .cuerpo b {{ color:var(--tinta); }}
.tarjeta-texto .cuerpo ul {{ margin:.4rem 0 0; padding-left:1.1rem; }}
.tarjeta-texto .cuerpo li {{ margin:.25rem 0; }}
.tarjeta-texto .pie {{ margin-top:.8rem; font-size:.8rem; color:var(--tenue); }}
.cifra-alerta {{ font-size: clamp(3rem, 5vw, 4.4rem); font-weight:700; letter-spacing:-.045em; line-height:1;
  color:var(--tinta); margin:.5rem 0 .2rem; }}
.cifra-alerta small {{ font-size:.45em; color:var(--tinta-2); font-weight:600; }}
.estado-critico {{ display:inline-flex; align-items:center; gap:.4rem; font-size:.75rem; font-weight:700;
  letter-spacing:.06em; text-transform:uppercase; color:#d03b3b; }}
.veredictos {{ display:grid; gap:.55rem; margin:1.1rem 0 .6rem; padding-top:1rem; border-top:1px solid var(--grilla); }}
.veredictos div {{ display:grid; grid-template-columns: 9.5rem 1fr; gap:.6rem; font-size:.84rem; line-height:1.4; }}
.veredictos b {{ color:var(--tinta); font-weight:600; }}
.veredictos span {{ color:var(--tinta-2); }}
.conclusion {{ background: var(--superficie); border:1px solid var(--borde); border-left:4px solid var(--acento);
  border-radius:16px; padding:1.4rem 1.6rem; }}
.conclusion .kicker {{ font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; color:var(--acento);
  font-weight:700; }}
.conclusion h3 {{ font-size:1.4rem; font-weight:650; letter-spacing:-.02em; color:var(--tinta);
  margin:.35rem 0 .5rem; padding:0; line-height:1.25; }}
.conclusion p, .conclusion li {{ color:var(--tinta-2); font-size:.97rem; line-height:1.55; }}
.conclusion b {{ color:var(--tinta); }}
.acciones {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr)); gap:.8rem; }}
.accion {{ background:var(--superficie); border:1px solid var(--borde); border-radius:16px; padding:1.2rem 1.25rem;
  display:flex; flex-direction:column; gap:.45rem; }}
.accion .num {{ font-size:1.9rem; font-weight:300; color:var(--acento); line-height:1; letter-spacing:-.04em;
  font-variant-numeric: tabular-nums; }}
.accion h4 {{ font-size:1.05rem; font-weight:650; color:var(--tinta); margin:.2rem 0 0; padding:0; line-height:1.3;
  letter-spacing:-.01em; }}
.accion p {{ color:var(--tinta-2); font-size:.88rem; line-height:1.5; margin:0; flex:1; }}
.accion .evidencia {{ border-top:1px solid var(--grilla); padding-top:.6rem; margin-top:.3rem; font-size:.82rem;
  color:var(--tinta); line-height:1.4; }}
.accion .evidencia span {{ display:block; font-size:.68rem; letter-spacing:.08em; text-transform:uppercase;
  color:var(--tenue); font-weight:600; margin-bottom:.2rem; }}
.chip-filtro {{ display:inline-block; font-size:.78rem; color:var(--tinta-2); margin:.1rem 0 .2rem; }}
.chip-filtro b {{ color: var(--acento); font-weight:600; }}
"""
    if not oscuro:
        return base
    # Streamlit aplica el tema claro de .streamlit/config.toml; en oscuro se sobreescriben
    # las superficies de los widgets que usa la app.
    return base + f"""
.stApp, .stApp p, .stApp label, .stApp span, .stMarkdown {{ color: var(--tinta); }}
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="input"] input,
[data-baseweb="base-input"], [data-testid="stDateInputField"] {{
  background-color: {t.pagina} !important; border-color: {t.eje} !important; color: var(--tinta) !important; }}
[data-baseweb="select"] svg, [data-baseweb="input"] svg {{ fill: var(--tenue) !important; }}
[data-baseweb="select"] div, [data-baseweb="select"] input {{ color: var(--tinta-2) !important;
  caret-color: var(--tinta) !important; }}
[data-baseweb="tag"] {{ background-color: color-mix(in srgb, var(--acento) 22%, {t.superficie}) !important; }}
[data-baseweb="tag"] span {{ color: var(--tinta) !important; }}
[data-baseweb="popover"] > div, [data-baseweb="popover"] ul, [data-baseweb="menu"],
[data-baseweb="calendar"], [data-baseweb="calendar"] > div, [data-baseweb="calendar"] div[role="grid"] * {{
  background-color: {t.superficie} !important; color: var(--tinta) !important; }}
[data-baseweb="popover"] li, [data-baseweb="popover"] li *, [role="option"], [role="option"] * {{
  color: var(--tinta) !important; }}
[data-baseweb="popover"] li:hover,[data-baseweb="popover"] li[aria-selected="true"] {{
  background-color: {t.eje} !important; }}
[data-baseweb="calendar"] [aria-selected="true"] div, [data-baseweb="calendar"] [aria-selected="true"] {{
  background-color: var(--acento) !important; color: #fff !important; }}
[data-testid*="stBaseButton-segmented_control"], [data-testid="stBaseButton-secondary"],
[data-testid*="stBaseButton-pills"] {{
  background-color: {t.pagina} !important; border-color: {t.eje} !important; color: var(--tinta-2) !important; }}
[data-testid="stBaseButton-segmented_controlActive"], [data-testid="stBaseButton-pillsActive"] {{
  background-color: color-mix(in srgb, var(--acento) 25%, {t.superficie}) !important;
  border-color: var(--acento) !important; color: var(--tinta) !important; }}
[data-testid="stBaseButton-secondary"]:hover {{ border-color: var(--acento) !important; color: var(--tinta) !important; }}
[data-testid="stTooltipContent"], [data-baseweb="tooltip"] > div {{ background:{t.superficie} !important; color: var(--tinta) !important; }}
[data-testid="stExpander"] details {{ background: var(--superficie); border-color: var(--borde); }}
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapsedControl"] svg, [data-testid="stExpandSidebarButton"] svg {{ fill: var(--tinta-2) !important; color: var(--tinta-2) !important; }}
[data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] {{ color: var(--tinta-2) !important; }}
"""

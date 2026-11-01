"""Anexo · Auditoría del dato: qué hizo el pipeline con el CSV crudo y si los datos salieron intactos.

Describe el dataset completo: los filtros de la barra lateral no aplican aquí.
"""

import streamlit as st

from air_quality import cargar_crudo
from air_quality.auditoria import TOPE_DELTA_SPEARMAN, auditar, rango

import componentes as ui
import graficos

FASES = {"I-claves": "Claves", "III-duplicados": "Duplicados", "III-nulos": "Nulos", "IV": "Transformación"}


@st.cache_data(show_spinner="Auditando el pipeline sobre el CSV crudo…")
def _auditoria():
    return auditar(cargar_crudo())


def render(t):
    a = _auditoria()
    r = a.resumen
    v = a.verificaciones
    fallan = v[~v["aprobado"]]
    pct_dup = r["duplicados"] / r["filas_crudo"] * 100
    titulo = (f"El pipeline quitó {pct_dup:.0f} % de filas duplicadas sin deformar los datos"
              + (f"; solo falla {'la ' + fallan.iloc[0]['control'].lower() if len(fallan) == 1 else f'{len(fallan)} controles'}"
                 if len(fallan) else ""))
    ui.capitulo(
        "A", "auditoria", "Anexo · Auditoría del dato", titulo,
        "De dónde salen las 5,075 mediciones del tablero: qué se limpió del CSV crudo, qué se imputó y "
        "qué controles de calidad pasa el resultado. Describe el dataset completo, así que los filtros "
        "de la barra lateral no aplican en esta página.", activos=False)

    # --- Antes → después -------------------------------------------------------------------------
    ui.kpis([
        dict(rotulo="Filas", valor=f"{r['filas_procesado']:,}",
             nota=f"de <b>{r['filas_crudo']:,}</b> en el crudo: el {pct_dup:.0f} % eran duplicados"),
        dict(rotulo="Ciudades", valor=str(r["ciudades"]),
             nota=f"de <b>{r['variantes_ciudad']}</b> variantes de escritura (mayúsculas, espacios, tildes)"),
        dict(rotulo="Celdas nulas", valor=f"{r['nulos_procesado']:,}",
             nota=(f"de <b>{r['nulos_crudo']:,}</b>: {r['nulos_con_duplicados']:,} se fueron con los duplicados "
                   f"y solo <b>{r['nulos_imputados']}</b> se imputaron")),
        dict(rotulo="Decisiones registradas", valor=str(r["decisiones"]),
             nota="cada una con su justificación en la bitácora (abajo)"),
    ], columnas=4)

    c_emb, c_ver = st.columns([6, 6], gap="medium")
    with c_emb, st.container(key="tarjeta-embudo", height="stretch"):
        ui.titulo_grafico("Del CSV crudo al procesado",
                          "Filas que quedan tras cada paso. Primero se quitan los duplicados exactos (toda la "
                          "fila repetida); después, las filas que repiten ciudad y fecha con valores distintos, "
                          "de las que se conserva la más completa.")
        st.plotly_chart(graficos.embudo(a.embudo, t), key="g_embudo", config=graficos.CONFIG, theme=None)
        minimo, mediana, maximo = rango(a.nulos_ciudad)
        ui.nota(f"Los nulos del crudo estaban repartidos de forma pareja: entre el {minimo:.1f} % y el "
                f"{maximo:.1f} % por ciudad y contaminante (mediana {mediana:.1f} %). Ninguna ciudad perdió "
                "más información que otra.")
    with c_ver, st.container(key="tarjeta-verificaciones", height="stretch"):
        ui.titulo_grafico("Controles de calidad del CSV procesado",
                          f"{int(v['aprobado'].sum())} de {len(v)} controles aprobados. El que falla no se "
                          "corrigió a propósito: es un problema de la fuente, no del pipeline.")
        ui.verificaciones(v)

    # --- Distribuciones --------------------------------------------------------------------------
    ui.subseccion("¿La limpieza deformó los datos?", "Cada variable conserva su forma",
                  "Si quitar duplicados o imputar nulos hubiera sesgado una variable, su media o su "
                  "dispersión se moverían y la prueba de Kolmogorov-Smirnov (KS) detectaría que la "
                  "distribución cambió.")
    c_delta, c_txt = st.columns([8, 4], gap="medium")
    with c_delta, st.container(key="tarjeta-deltas"):
        ui.titulo_grafico("Cambio de la media y la desviación tras el pipeline",
                          "Crudo (con duplicados y nulos) frente al procesado. A la derecha, el p de la "
                          "prueba KS: p > 0.05 significa que no hay evidencia de que la distribución cambió.")
        st.plotly_chart(graficos.deltas_distribucion(a.distribuciones, t), key="g_deltas",
                        config=graficos.CONFIG, theme=None)
    with c_txt, st.container(key="tarjeta-deltas-texto", height="stretch"):
        d = a.distribuciones
        mayor = d.loc[d["delta_media_pct"].abs().idxmax()]
        nombre_mayor = graficos.NOMBRES_VARIABLE.get(mayor["variable"], mayor["variable"])
        cambio_mayor = ui.sin_corte(f"{mayor['delta_media_pct']:+.1f} %")
        ui.tarjeta_texto(
            "Lectura", "Los cambios son mínimos",
            f"El mayor movimiento es la media de <b>{nombre_mayor}</b> ({cambio_mayor}), "
            "y la prueba KS no distingue ninguna variable de su versión "
            f"cruda (p mínima = {d['ks_p'].min():.2f}).<ul>"
            f"<li>Las correlaciones tampoco cambiaron: la mayor diferencia en Spearman es "
            f"{r['delta_spearman']:.3f} (umbral {TOPE_DELTA_SPEARMAN}).</li>"
            "<li>Entre contaminantes las correlaciones son casi nulas (|ρ| &lt; 0.03): cada uno varía por su "
            "cuenta, por eso no se muestra una matriz de correlación.</li></ul>")

    # --- Bitácora --------------------------------------------------------------------------------
    ui.subseccion("Trazabilidad", "Bitácora de decisiones",
                  "Cada paso del pipeline registra qué hizo y por qué. Es la misma bitácora que genera "
                  "<code>air_quality.pipeline.ejecutar</code>.")
    with st.container(key="tarjeta-bitacora"):
        fase = st.segmented_control("Fase", ["Todas"] + list(FASES.values()), key="aud_fase",
                                    default="Todas", label_visibility="collapsed")
        b = a.bitacora.copy()
        b["fase"] = b["fase"].map(lambda x: FASES.get(x, x))
        if fase and fase != "Todas":
            b = b[b["fase"] == fase]
        ui.tabla_simple(b.rename(columns={"fase": "Fase", "columna": "Columna", "accion": "Acción",
                                          "justificacion": "Justificación"}), alto_max=480)

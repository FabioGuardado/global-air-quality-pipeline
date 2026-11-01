"""Capítulo 04 · Recomendación: cuánto habría que recortar, dónde empezar y qué hacer."""

import pandas as pd
import streamlit as st

from air_quality import recomendacion as rc
from air_quality.metricas import nombre_ciudad
from air_quality.patrones import integridad_sensor
from air_quality.severidad import clasificar, guia, niveles

import componentes as ui
import graficos
from filtros import ETIQUETA_CONT, alternar_ciudad, ciudad_de_seleccion, describir

COLUMNAS_DETALLE = {
    "City": "Ciudad", "Country": "País", "region": "Región", "Date": "Fecha",
    "PM2.5": "PM2.5 (µg/m³)", "PM10": "PM10 (µg/m³)", "NO2": "NO2 (µg/m³)",
    "n_excedencias_oms": "Guías superadas", "Temperature": "Temperatura (°C)",
    "Humidity": "Humedad (%)", "Wind Speed": "Viento (km/h)",
}
FILAS_VISIBLES = 300


def _al_seleccionar():
    ciudad = ciudad_de_seleccion(st.session_state.get("sel_ranking"), 3)
    if ciudad:
        alternar_ciudad(ciudad)


def _meta_alcanzable(req, reduccion):
    """La meta más exigente que alcanza el escenario (o None)."""
    ok = req[req["reduccion"] <= reduccion + 1e-9]
    return ok.iloc[-1] if not ok.empty else None


def render(df, df_contexto, f, t):
    cont = f.contaminante
    et = ETIQUETA_CONT[cont]
    if df.empty:
        ui.capitulo("04", "recomendacion", "Recomendación", "Sin datos para esta combinación de filtros")
        ui.vacio()
        return

    req = rc.reduccion_necesaria(df, cont)
    r_guia = float(req["reduccion"].iloc[-1])
    r_it1 = float(req["reduccion"].iloc[0])
    contexto = describir(f)
    titulo = (f"Cumplir la guía exige recortar un {r_guia:.0f} % la contaminación de fondo: el camino es por etapas"
              if r_guia >= 1 else "Estos días ya cumplen la guía: el reto es mantenerlos")
    ui.capitulo(
        "04", "recomendacion", "Recomendación", titulo,
        f"{'En ' + contexto + ', l' if contexto else 'L'}a OMS fija metas intermedias (IT-1 a IT-4) "
        "precisamente para los lugares que están lejos de la guía. Llegar a IT-1, la primera, ya exige un "
        f"recorte del <b>{r_it1:.0f} %</b> de {et}. Mueve el escenario para ver qué se gana en cada etapa.")

    # --- Simulador ---------------------------------------------------------------------------
    c_sim, c_ruta = st.columns([6, 6], gap="medium")
    with c_sim, st.container(key="tarjeta-simulador", height="stretch"):
        ui.titulo_grafico("Simulador de reducción",
                          "Recorte proporcional de todas las concentraciones diarias, como si las fuentes "
                          "permanentes emitieran ese porcentaje menos.")
        reduccion = st.slider("Recorte de las emisiones de fondo", 0, 95, 40, 5, key="sim_reduccion",
                              format="−%d %%")
        sim = rc.simular(df, cont, reduccion)
        e = rc.resumen_escenario(sim)
        dias_ganados = round((e["guia_despues"] - e["guia_antes"]) / 100 * len(df))
        ui.kpis([
            dict(rotulo="Días que cumplen la guía", valor=ui.fmt_pct(e["guia_despues"], 0), unidad="%",
                 nota=f"hoy son el <b>{e['guia_antes']:.0f} %</b>: <b>{dias_ganados:+,}</b> días-ciudad",
                 color=t.severidad[0]),
            dict(rotulo="Días sobre IT-1", valor=ui.fmt_pct(e["it1_despues"], 0), unidad="%",
                 nota=f"hoy son el <b>{e['it1_antes']:.0f} %</b>, el tramo más severo",
                 color=t.severidad[5]),
        ])
        ui.titulo_grafico("Cómo se reparten los días por nivel OMS")
        ui.leyenda_severidad(niveles(cont), t.severidad)
        st.plotly_chart(graficos.antes_despues(sim, cont, t, reduccion), key="g_antes_despues",
                        config=graficos.CONFIG, theme=None)
        if f.niveles:
            ui.nota("Con el filtro de severidad activo, el escenario parte solo de los días de esos niveles.")

    with c_ruta, st.container(key="tarjeta-ruta", height="stretch"):
        ui.titulo_grafico("Hoja de ruta: recorte necesario para cada meta",
                          f"Una meta se cumple cuando el 99 % de los días queda en o bajo su valor (así "
                          f"define la OMS la guía de 24 h). En azul, las que alcanza el escenario de −{reduccion} %.")
        st.plotly_chart(graficos.hoja_ruta(req, cont, t, reduccion), key="g_hoja_ruta",
                        config=graficos.CONFIG, theme=None)
        meta = _meta_alcanzable(req, reduccion)
        if meta is None:
            cuerpo = (f"Un recorte del {reduccion} % todavía no alcanza ninguna meta: en los peores días "
                      f"{et} sigue sobre {ui.sin_corte('IT-1')}. Hace falta al menos un <b>{r_it1:.0f} %</b> para la primera etapa.")
        elif meta["meta"] == "guía":
            cuerpo = (f"Con −{reduccion} % se cumple la guía de la OMS. Es un recorte enorme: equivale a "
                      "eliminar casi toda la emisión de fondo, algo que ninguna medida puntual consigue.")
        else:
            siguiente = req.iloc[req.index.get_loc(meta.name) + 1]
            cuerpo = (f"Con −{reduccion} % se alcanza <b>{meta['meta']}</b> ({meta['valor']:g} µg/m³). "
                      f"La siguiente etapa, {graficos._etiqueta_meta(siguiente['meta'], siguiente['valor'])}, "
                      f"pide un <b>{siguiente['reduccion']:.0f} %</b>. Cada escalón es más caro que el anterior, "
                      "por eso conviene fijar plazos por etapa.")
        ui.html(f'<p class="sub-graf" style="margin:.4rem 0 0">{cuerpo}</p>')
        ui.nota("Supuesto: rollback proporcional. Es razonable aquí porque el capítulo 03 no encontró "
                "factores externos que modulen la contaminación, pero no modela química atmosférica ni "
                "transporte entre ciudades.")

    # --- Dónde empezar ------------------------------------------------------------------------
    pri = rc.prioridad_ciudades(df_contexto, cont)
    ui.subseccion("Dónde actuar primero", "Las ciudades, ordenadas por días críticos",
                  "Un día crítico supera a la vez las guías de PM₂.₅, PM₁₀ y NO₂: toda la mezcla está alta. "
                  "Es el indicador que no depende del contaminante elegido.")
    c_rank, c_rank_txt = st.columns([7, 5], gap="medium")
    with c_rank, st.container(key="tarjeta-ranking"):
        ui.titulo_grafico("% de días críticos por ciudad",
                          "Clic en una ciudad para filtrar todo el tablero; clic de nuevo para quitar el filtro.")
        st.plotly_chart(graficos.ranking_ciudades(pri, t, f.ciudades), key="sel_ranking",
                        on_select=_al_seleccionar, selection_mode="points", config=graficos.CONFIG,
                        theme=None)
    with c_rank_txt, st.container(key="tarjeta-ranking-texto", height="stretch"):
        if len(pri) > 1:
            primera, ultima = pri.iloc[0], pri.iloc[-1]
            brecha = primera["pct_criticos"] - ultima["pct_criticos"]
            top = ", ".join(nombre_ciudad(c) for c in pri["City"].head(3))
            cuerpo = (f"Las tres primeras son <b>{top}</b>. Pero entre la primera "
                      f"({primera['pct_criticos']:.0f} %) y la última ({ultima['pct_criticos']:.0f} %) hay "
                      f"solo <b>{brecha:.0f} puntos</b>. "
                      + ("El orden sirve para secuenciar el despliegue, no para concentrar recursos: "
                         "ninguna ciudad puede quedar fuera del plan." if brecha < 15 else
                         "La diferencia es suficiente para concentrar recursos en las primeras."))
        else:
            fila = pri.iloc[0]
            cuerpo = (f"<b>{nombre_ciudad(fila['City'])}</b> tiene el {fila['pct_criticos']:.0f} % de sus días "
                      f"en estado crítico y necesitaría un recorte del {fila['reduccion_guia']:.0f} % para "
                      f"cumplir la guía de {et}.")
        ui.tarjeta_texto("Lectura", "Priorizar sin excluir", cuerpo)
        ui.titulo_grafico("Primeras cinco ciudades")
        top5 = pri.head(5)
        ui.tabla_simple(pd.DataFrame({
            "Ciudad": top5["City"].map(nombre_ciudad),
            "Críticos (días)": top5["dias_criticos"],
            "Sobre IT-1 (%)": top5["pct_sobre_it1"].round(0).astype(int),
            "Recorte a guía (%)": top5["reduccion_guia"].round(0).astype(int),
        }))
        ui.nota(f"Recorte a guía: el que necesita cada ciudad para cumplir la guía de {et} el 99 % de los días.")
        if len(f.ciudades) == 1 and len(pri) > 1 and f.ciudades[0] in set(pri["City"]):
            puesto = int(pri.index[pri["City"] == f.ciudades[0]][0]) + 1
            ui.html(f'<p class="chip-filtro">Seleccionada: <b>{nombre_ciudad(f.ciudades[0])}</b>, '
                    f'puesto {puesto} de {len(pri)}</p>')

    # --- Qué hacer ----------------------------------------------------------------------------
    pct_imp, _ = integridad_sensor(df)
    nv = niveles(cont)
    pct_it1 = (df[cont] > nv[-1].desde).mean() * 100
    ui.subseccion("Qué hacer", "Cuatro decisiones que se desprenden de la evidencia",
                  "Cada recomendación cita el hallazgo que la respalda y el capítulo donde se ve.")
    ui.acciones([
        dict(num="1", titulo="Atacar las fuentes permanentes",
             cuerpo="Tráfico, industria y generación de energía: normas de emisión, zonas de bajas emisiones "
                    "y transición energética. Las restricciones por episodio o por temporada tienen poco margen.",
             evidencia="Ni el clima, ni la estación, ni el fin de semana mueven la aguja", cap="03"),
        dict(num="2", titulo="Avanzar por metas intermedias",
             cuerpo=f"Fijar plazos por etapa: primero {ui.sin_corte(f'IT-1 (−{r_it1:.0f} %)')}, después IT-2 y "
                    f"así hasta la guía {ui.sin_corte(f'(−{r_guia:.0f} %)')}. Una meta alcanzable sostiene la "
                    "voluntad política; la guía de una vez, no.",
             evidencia=f"Hoy el {pct_it1:.0f} % de los días ni siquiera alcanza {ui.sin_corte('IT-1')}", cap="01"),
        dict(num="3", titulo="Recalibrar la red de sensores",
             cuerpo="Auditar la calibración y el procesamiento comunes a toda la red antes de usar la relación "
                    "PM₂.₅/PM₁₀ para decidir, y publicar un control de calidad periódico.",
             evidencia=f"El {pct_imp:.0f} % de las lecturas tiene PM₂.₅ &gt; PM₁₀, algo físicamente imposible",
             cap="02"),
        dict(num="4", titulo="Alertar por nivel OMS, no por guía",
             cuerpo="Una alerta cada vez que se supera la guía sonaría casi todos los días y dejaría de "
                    "escucharse. Escalonar los avisos por nivel IT y reservar las medidas de protección "
                    "(grupos sensibles, actividad al aire libre) para los niveles altos.",
             evidencia=f"La guía se supera el {(df[cont] > guia(cont)).mean() * 100:.0f} % de los días", cap="01"),
    ])

    # --- Detalle a demanda: tabla y exportación -----------------------------------------------
    ui.subseccion("Detalle a demanda", "Los datos detrás del tablero",
                  "Las mediciones que cumplen todos los filtros activos, con su nivel OMS. La descarga "
                  "incluye todas las filas.")
    with st.container(key="tarjeta-detalle"):
        tabla = _tabla_detalle(df, cont)
        c_info, c_boton = st.columns([8, 2], vertical_alignment="center")
        c_info.html(f'<p class="sub-graf" style="margin:0"><b>{len(tabla):,}</b> mediciones · '
                    f'{df["City"].nunique()} ciudades'
                    + (f' · se muestran las primeras {FILAS_VISIBLES}' if len(tabla) > FILAS_VISIBLES else "")
                    + '</p>')
        c_boton.download_button("Descargar CSV", tabla.to_csv(index=False).encode("utf-8-sig"),
                                file_name="calidad_aire_filtrado.csv", mime="text/csv",
                                key="descarga_csv", icon=":material/download:", use_container_width=True)
        vista = tabla.head(FILAS_VISIBLES).copy()
        vista["Fecha"] = vista["Fecha"].dt.strftime("%d/%m/%Y")
        ui.tabla_simple(vista.round(1), alto_max=420)


def _tabla_detalle(df, cont):
    d = df[list(COLUMNAS_DETALLE)].sort_values(["City", "Date"]).copy()
    d["City"] = d["City"].map(nombre_ciudad)
    d["Country"] = d["Country"].map(nombre_ciudad)
    d.insert(d.columns.get_loc(cont) + 1, f"Nivel OMS {cont}", clasificar(d[cont], cont).astype(str).values)
    return d.rename(columns=COLUMNAS_DETALLE).reset_index(drop=True)

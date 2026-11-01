"""Capítulo 03 · Causa raíz: se ponen a prueba las explicaciones habituales y se descartan con evidencia."""

import streamlit as st

from air_quality import hipotesis as hp

import componentes as ui
import graficos
from filtros import ETIQUETA_CONT, describir

DETALLES = ["Meteorología", "Estación", "Fin de semana", "Ciudad"]
NOMBRE_CORTO = {"Viento": "el viento", "Temperatura": "el calor", "Humedad": "la humedad",
                "Estación": "la estación", "Fin de semana": "el fin de semana", "Ciudad": "la ciudad"}


def _lista(nombres):
    nombres = [NOMBRE_CORTO.get(n, n.lower()) for n in nombres]
    if len(nombres) <= 1:
        return "".join(nombres)
    return ", ".join(nombres[:-1]) + " ni " + nombres[-1]


def render(df, f, t):
    cont = f.contaminante
    et = ETIQUETA_CONT[cont]
    if df.empty:
        ui.capitulo("03", "causa", "Causa raíz", "Sin datos para esta combinación de filtros")
        ui.vacio()
        return

    ev = hp.evaluar(df, cont)
    descartadas = ev.loc[ev["veredicto"] == "Descartada", "factor"].tolist()
    confirmadas = ev.loc[ev["veredicto"] == "Confirmada", "factor"].tolist()
    if confirmadas:
        titulo = (f"{_lista(confirmadas).capitalize()} sí marca{'n' if len(confirmadas) > 1 else ''} "
                  "una diferencia relevante")
    elif descartadas:
        clave = [d for d in ["Viento", "Temperatura", "Fin de semana"] if d in descartadas] or descartadas[:3]
        titulo = f"Ni {_lista(clave)} explican la contaminación"
    else:
        titulo = "Ningún factor alcanza un efecto relevante"
    contexto = describir(f)
    ui.capitulo(
        "03", "causa", "Causa raíz", titulo,
        f"{'En ' + contexto + ', s' if contexto else 'S'}e pusieron a prueba seis explicaciones habituales "
        f"de la contaminación por {et}. Cada una debe superar dos filtros: que la diferencia sea "
        "<b>real</b> (prueba estadística, p &lt; 0.05) y que <b>importe</b> (más del 10 % de la mediana). "
        f"{len(descartadas)} de {len(ev[ev['veredicto'] != 'No aplica'])} no superan ni el primero.")

    c_graf, c_lectura = st.columns([8, 4], gap="medium")
    with c_graf, st.container(key="tarjeta-efectos"):
        ui.titulo_grafico("Marcador de hipótesis",
                          "Cuánto cambia la mediana entre el grupo más y el menos contaminado de cada "
                          "factor. Los continuos se comparan por cuartiles. Pasa el cursor para ver la prueba.")
        st.plotly_chart(graficos.efectos(ev, t), key="g_efectos", config=graficos.CONFIG, theme=None)
        if f.niveles:
            ui.nota("Con el filtro de severidad activo, las pruebas se calculan sobre un rango de valores "
                    "recortado: el efecto de cualquier factor tiende a encogerse.")
    with c_lectura, st.container(key="tarjeta-lectura-causa", height="stretch"):
        trampa = ev[(ev["efecto"] >= ev["umbral"]) & (ev["veredicto"] == "Descartada")]
        if not trampa.empty:
            x = trampa.iloc[0]
            cuerpo = (f"<b>{x['factor']}</b> muestra la mayor diferencia: {x['efecto']:.0f} µg/m³ entre "
                      f"{graficos._bonito(x['grupo_min'])} y {graficos._bonito(x['grupo_max'])}, por encima del "
                      f"umbral. Pero p = {x['p']:.2f}: con unos {int(len(df) / max(x['n_grupos'], 1))} días por "
                      "grupo, diferencias de ese tamaño aparecen por puro azar. <b>Una diferencia grande "
                      "sin significancia no es evidencia.</b>")
        else:
            cuerpo = ("Un factor solo explica la contaminación si la diferencia es estadísticamente real "
                      "<b>y</b> lo bastante grande para importar. La franja gris marca lo que se considera "
                      "despreciable.")
        ui.tarjeta_texto("Cómo leerlo", "Tamaño y significancia, juntos", cuerpo)
        ui.html(f"""
<div class="veredictos">
  <div><b>✓ Confirmada</b><span>diferencia real (p &lt; 0.05) y mayor que el umbral</span></div>
  <div><b>≈ Real pero menor</b><span>real, pero dentro de la franja despreciable</span></div>
  <div><b>✕ Descartada</b><span>no se distingue del azar (p ≥ 0.05)</span></div>
  <div><b>– No aplica</b><span>el filtro deja un solo grupo para comparar</span></div>
</div>
<p class="nota-graf">Spearman para viento, temperatura y humedad; Kruskal-Wallis para estación y ciudad;
Mann-Whitney para fin de semana. No paramétricas porque los datos no son normales (Fase II).</p>""")

    # --- Detalle a demanda ----------------------------------------------------------------
    ui.subseccion("Detalle a demanda", "La evidencia de cada hipótesis",
                  "Punto: mediana. Bigote: rango intercuartil (50 % central de los días). Todos los ejes "
                  "empiezan en 0 y la línea discontinua es la guía OMS: las diferencias se ven en su "
                  "proporción real.")
    detalle = st.segmented_control("Ver detalle", DETALLES, key="det_causa", default="Meteorología",
                                   label_visibility="collapsed")
    with st.container(key="tarjeta-detalle-causa"):
        _detalle(detalle or "Meteorología", df, cont, t)

    ui.html(f"""
<div class="conclusion">
  <div class="kicker">Lo que queda en pie</div>
  <h3>Si nada externo mueve la aguja, la contaminación es de fondo y constante</h3>
  <p>Ni el clima ni el calendario la modulan: no baja con viento, no sube con calor, no descansa el fin
  de semana ni cambia con la estación. Lo que queda es un nivel base sostenido, propio de
  <b>fuentes permanentes</b> (tráfico, industria, generación de energía) que emiten todos los días.
  Por eso las medidas puntuales o estacionales tienen poco margen: la respuesta tiene que ser
  <b>estructural</b>.</p>
</div>""")


def _detalle(cual, df, cont, t):
    if cual == "Meteorología":
        tablas = {n: hp.grupos(df, cont, n) for n in ["Viento", "Temperatura", "Humedad"]}
        ui.titulo_grafico(f"{cont} por cuartil de cada variable meteorológica",
                          "Si el viento dispersara o el calor concentrara contaminantes, los puntos subirían "
                          "o bajarían de izquierda a derecha.")
        st.plotly_chart(graficos.grupos(tablas, cont, t), key="g_det_meteo", config=graficos.CONFIG,
                        theme=None)
    elif cual == "Estación":
        ui.titulo_grafico(f"{cont} por trimestre meteorológico",
                          "Trimestres del hemisferio norte; las ciudades del sur (Sydney, Johannesburgo, "
                          "Río) tienen las estaciones invertidas, y aun así no aparece patrón.")
        st.plotly_chart(graficos.grupos({"Estación": hp.grupos(df, cont, "Estación")}, cont, t),
                        key="g_det_estacion", config=graficos.CONFIG, theme=None)
    elif cual == "Fin de semana":
        d = hp.finde_por_ciudad(df, cont)
        if d.empty:
            ui.vacio("No hay suficientes días laborables y de fin de semana para comparar.", "")
            return
        sig = int((d["p"] < hp.ALFA).sum())
        dias_finde = int(df[df["fin_semana"]].groupby("City", observed=True).size().median())
        ui.titulo_grafico(
            "Laborables frente a fines de semana, ciudad por ciudad",
            f"Menos tráfico el fin de semana debería bajar la contaminación. "
            f"{'Ninguna' if sig == 0 else sig} de las {len(d)} diferencias es estadísticamente significativa "
            f"(p mínima = {d['p'].min():.2f}): las que se ven son ruido de muestras de unos {dias_finde} "
            "fines de semana por ciudad.")
        st.plotly_chart(graficos.dumbbell_finde(d, cont, t), key="g_det_finde", config=graficos.CONFIG,
                        theme=None)
    else:
        g = hp.grupos(df, cont, "Ciudad")
        if len(g) < 2:
            ui.vacio("Con una sola ciudad seleccionada no hay comparación entre ciudades.",
                     "Quita el filtro de ciudad para ver esta vista.")
            return
        ui.titulo_grafico(f"{cont} por ciudad",
                          "Los rangos intercuartiles se superponen casi por completo: ninguna ciudad se separa "
                          "del resto.")
        st.plotly_chart(graficos.grupos_horizontal(g, cont, t, df[cont].median()), key="g_det_ciudad",
                        config=graficos.CONFIG, theme=None)

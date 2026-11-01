"""Capítulo 02 · Patrones y anomalías (zoom and filter): cuándo aparecen y qué no cuadra."""

import streamlit as st

from air_quality import patrones as pt
from air_quality.metricas import nombre_ciudad
from air_quality.severidad import clasificar, niveles

import componentes as ui
import graficos
from filtros import ETIQUETA_CONT, describir


def _nivel_de(contaminante):
    nv = {n.nombre: n.indice for n in niveles(contaminante)}

    def nombre_nivel(valor):
        nombre = clasificar([valor], contaminante).iloc[0]
        return nombre, nv[nombre]
    return nombre_nivel


def render(df, df_contexto, f, t):
    cont = f.contaminante
    et = ETIQUETA_CONT[cont]
    if df.empty:
        ui.capitulo("02", "patrones", "Patrones y anomalías", "Sin datos para esta combinación de filtros")
        ui.vacio()
        return

    mes = pt.por_mes(df, cont)
    ep = pt.episodios(df, cont)
    it1 = niveles(cont)[-1].desde
    racha = pt.rachas(df, cont, it1)
    peor = mes.loc[mes["pct_sobre_guia"].idxmin()] if not mes.empty else None

    if peor is not None and len(mes) >= 3 and peor["pct_sobre_guia"] >= 75:
        titulo = (f"No hay temporada limpia: hasta el mejor mes supera la guía "
                  f"el {peor['pct_sobre_guia']:.0f} % de los días")
    elif peor is not None and len(mes) >= 3:
        titulo = (f"{peor['nombre']} es el mes con más alivio, pero aún supera la guía "
                  f"el {peor['pct_sobre_guia']:.0f} % de los días")
    else:
        titulo = "En el periodo elegido la contaminación no da respiro"
    r0 = racha.iloc[0] if not racha.empty else None
    texto_racha = (f"la racha más larga sobre IT-1 dura <b>{int(r0['dias'])} días</b> "
                   f"({nombre_ciudad(r0['City'])})" if r0 is not None and r0["dias"] > 0
                   else "no hay rachas sobre IT-1")
    contexto = describir(f)
    ui.capitulo(
        "02", "patrones", "Patrones y anomalías", titulo,
        f"{'En ' + contexto + ', e' if contexto else 'E'}l color del calendario apenas cambia de enero "
        f"a diciembre ni de una ciudad a otra. Hay picos ({len(ep):,} días por encima del percentil 95 "
        f"de su propia ciudad), pero son breves: {texto_racha}.")

    # --- Calendario ciudad × semana (contexto: todas las ciudades) ------------------------
    cal = pt.calendario(df_contexto, cont)
    orden = (df_contexto.assign(City=df_contexto["City"].astype(str))
             .groupby("City")[cont].median().sort_values(ascending=False).index.tolist())
    with st.container(key="tarjeta-calendario"):
        ui.titulo_grafico(f"Mediana semanal de {et} en cada ciudad",
                          "Cada celda es una semana. Ciudades ordenadas de mayor a menor mediana anual; "
                          "la misma escala fija del mapa (0 a 2× IT-1). Las celdas vacías son semanas sin "
                          "mediciones.")
        st.plotly_chart(graficos.calendario(cal, cont, t, orden, f.ciudades), key="g_calendario",
                        config=graficos.CONFIG, theme=None)

    # --- Tendencia + estacionalidad ------------------------------------------------------
    c_tend, c_mes = st.columns([7, 5], gap="medium")
    movil = pt.serie_movil(df_contexto, cont)
    banda = pt.banda_ciudades(movil)
    with c_tend, st.container(key="tarjeta-tendencia"):
        if f.ciudades:
            sub = ("Media móvil de 7 días de " + ", ".join(nombre_ciudad(c) for c in f.ciudades[:3])
                   + " frente a la mediana y el rango intercuartil (gris) de las ciudades. "
                   "Los rombos marcan sus episodios.")
        else:
            sub = ("Media móvil de 7 días: mediana de las ciudades y su rango intercuartil (gris). "
                   "Selecciona hasta 3 ciudades en el filtro para compararlas.")
        ui.titulo_grafico(f"Evolución diaria de {et}", sub)
        st.plotly_chart(graficos.tendencia(movil, banda, cont, t, f.ciudades, ep), key="g_tendencia",
                        config=graficos.CONFIG, theme=None)
        if len(f.ciudades) > 3:
            ui.nota("Se muestran las primeras 3 ciudades seleccionadas para mantener la lectura clara.")
    with c_mes, st.container(key="tarjeta-mes"):
        ui.titulo_grafico("Días sobre la guía, mes a mes",
                          "Si hubiera estacionalidad, algún mes bajaría con claridad. Eje completo de 0 a 100 %.")
        st.plotly_chart(graficos.barras_mes(mes, cont, t), key="g_mes", config=graficos.CONFIG, theme=None)

    # --- Episodios ------------------------------------------------------------------------
    ui.subseccion("Detalle a demanda", "El peor episodio de cada ciudad",
                  "Un episodio es un día por encima del percentil 95 de su propia ciudad: anómalo para "
                  "ese lugar, no solo alto en términos absolutos. La tabla muestra el más extremo de cada "
                  "ciudad; el listado completo está debajo.")
    c_tabla, c_kpi = st.columns([7, 5], gap="medium")
    with c_tabla, st.container(key="tarjeta-episodios"):
        if ep.empty:
            ui.vacio("No hay episodios con los filtros activos.", "")
        else:
            ui.tabla_episodios(ep.drop_duplicates("City"), cont, t.severidad, _nivel_de(cont))
            with st.expander(f"Ver los {len(ep):,} episodios"):
                tabla = ep.assign(City=ep["City"].map(nombre_ciudad),
                                  Date=ep["Date"].dt.strftime("%d/%m/%Y")).rename(columns={
                    "City": "Ciudad", "Date": "Fecha", "valor": f"{cont} (µg/m³)",
                    "umbral": "Umbral p95", "mediana_ciudad": "Mediana ciudad",
                    "veces_mediana": "× mediana"})
                ui.tabla_simple(tabla.round(2))
    with c_kpi:
        por_ciudad = ep.groupby("City").size().sort_values(ascending=False) if not ep.empty else None
        ui.kpis([
            dict(rotulo="Episodios", valor=f"{len(ep):,}", unidad="días",
                 nota=(f"el {len(ep) / len(df) * 100:.1f} % de los días medidos; "
                       f"máximo en {nombre_ciudad(por_ciudad.index[0])} ({por_ciudad.iloc[0]})"
                       if por_ciudad is not None else "ningún día supera el p95 de su ciudad")),
            dict(rotulo="Racha más larga sobre IT-1",
                 valor=str(int(r0["dias"])) if r0 is not None else "0", unidad="días",
                 nota=(f"{nombre_ciudad(r0['City'])}, del {ui.fecha(r0['desde'])} al {ui.fecha(r0['hasta'])}"
                       if r0 is not None and r0["dias"] > 0 else "sin días consecutivos sobre IT-1"),
                 color=t.severidad[5]),
            dict(rotulo="Pico máximo", valor=ui.fmt_num(df[cont].max()), unidad="µg/m³",
                 nota=f"{df[cont].max() / niveles(cont)[0].hasta:.0f}× la guía diaria"),
            dict(rotulo="Mes más contaminado",
                 valor=mes.loc[mes["pct_sobre_guia"].idxmax(), "nombre"] if not mes.empty else "—",
                 nota=(f"{mes['pct_sobre_guia'].max():.0f} % de días sobre la guía, apenas "
                       f"{mes['pct_sobre_guia'].max() - mes['pct_sobre_guia'].min():.0f} puntos más que el mejor"
                       if not mes.empty else "")),
        ])
        huecos = (df.sort_values("Date").groupby("City", observed=True)["Date"].diff().dt.days >= 2).mean() * 100
        ui.nota(f"Una racha solo cuenta días consecutivos medidos: el {huecos:.0f} % de las mediciones "
                "llega tras un hueco de 2 o más días, y un hueco corta la racha.")

    # --- Integridad del sensor -------------------------------------------------------------
    pct_imp, imp_ciudad = pt.integridad_sensor(df)
    ui.subseccion("Hallazgo de auditoría", "Una de cada tres lecturas de partículas es físicamente imposible",
                  "PM2.5 son las partículas de hasta 2.5 µm y forman parte de PM10 (hasta 10 µm): "
                  "PM2.5 nunca puede superar a PM10. Esta anomalía no se ve en ningún promedio; aparece "
                  "al cruzar las dos variables.")
    c_disp, c_txt = st.columns([7, 5], gap="medium")
    with c_disp, st.container(key="tarjeta-sensor"):
        ui.titulo_grafico("PM10 frente a PM2.5 en cada medición",
                          "Cada punto es un día-ciudad. Los que caen sobre la diagonal y = x son imposibles.")
        st.plotly_chart(graficos.dispersion_sensor(df, t), key="g_sensor", config=graficos.CONFIG,
                        theme=None)
    with c_txt, st.container(key="tarjeta-sensor-texto", height="stretch"):
        rango = (f"entre el <b>{imp_ciudad['pct_imposibles'].min():.0f} %</b> y el "
                 f"<b>{imp_ciudad['pct_imposibles'].max():.0f} %</b> según la ciudad"
                 if len(imp_ciudad) > 1 else "en la ciudad seleccionada")
        ui.html(f"""
<div class="estado-critico">⚠ Lecturas inválidas</div>
<div class="cifra-alerta">{ui.fmt_pct(pct_imp)}<small> %</small></div>
<p class="sub-graf">de las mediciones tiene PM2.5 &gt; PM10, {rango}.</p>""")
        ui.tarjeta_texto(
            "Qué significa", "Es sistemático, no una estación defectuosa",
            "Al repartirse de forma pareja entre todas las ciudades, apunta a un problema de calibración "
            "o de procesamiento común a toda la red, no a fallas puntuales.<ul>"
            "<li>Se marcó en la Fase I (<code>ratio_pm_imposible</code>), pero <b>no se eliminó</b>: "
            "descartar un tercio de los datos sesgaría todo el análisis.</li>"
            "<li>Las conclusiones sobre PM2.5 y PM10 por separado siguen en pie; lo que no es confiable "
            "es la <b>relación</b> entre ambas.</li></ul>",
            pie="La recomendación sobre recalibración está en el capítulo 04.")

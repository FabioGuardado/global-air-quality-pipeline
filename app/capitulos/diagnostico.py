"""Capítulo 01 · Diagnóstico (overview first): cuánto y dónde se incumple la guía OMS."""

import streamlit as st

from air_quality.metricas import distribucion_niveles, kpis, nombre_ciudad, por_ciudad
from air_quality.severidad import guia, niveles

import componentes as ui
import graficos
from filtros import ETIQUETA_CONT, alternar_ciudad, ciudad_de_seleccion, describir


def _fraccion_de_10(pct):
    return max(1, round(pct / 10)) if pct >= 5 else 0


def _al_seleccionar(clave, indice_custom):
    ciudad = ciudad_de_seleccion(st.session_state.get(clave), indice_custom)
    if ciudad:
        alternar_ciudad(ciudad)


def render(df, df_contexto, df_total, f, t):
    cont = f.contaminante
    et = ETIQUETA_CONT[cont]
    g = guia(cont)
    k, k0 = kpis(df, cont), kpis(df_total, cont)
    filtrado = len(df) != len(df_total)

    if k.n == 0:
        ui.capitulo("01", "diagnostico", "Diagnóstico", "Sin datos para esta combinación de filtros")
        ui.vacio()
        return

    n10 = _fraccion_de_10(k.pct_sobre_guia)
    titulo = (f"{n10} de cada 10 días el aire supera la guía de la OMS" if n10
              else "Casi todos los días se cumple la guía de la OMS")
    contexto = describir(f)
    bajada = (f"{'En ' + contexto + ', l' if contexto else 'L'}a mediana de {et} es "
              f"<b>{k.mediana:.0f} µg/m³</b>, {k.multiplo_guia:.1f} veces la guía diaria ({g:g} µg/m³). "
              f"Y en el <b>{k.pct_sobre_it1:.0f} %</b> de los días ni siquiera se alcanza la meta "
              f"intermedia más laxa de la OMS (IT-1).")
    ui.capitulo("01", "diagnostico", "Diagnóstico", titulo, bajada)

    # --- Cifra principal + KPIs ----------------------------------------------------------
    c_hero, c_kpis = st.columns([5, 7], gap="medium")
    with c_hero, st.container(key="tarjeta-hero", height="stretch"):
        ui.hero(cifra=ui.fmt_pct(k.pct_sobre_guia), unidad="%",
                rotulo=f"Días-ciudad sobre la guía OMS de {et}",
                texto=(f"de <b>{k.n:,}</b> mediciones diarias en <b>{k.n_ciudades}</b> "
                       f"{'ciudad' if k.n_ciudades == 1 else 'ciudades'} superan los "
                       f"<b>{g:g} µg/m³</b> que la OMS fija como límite de 24 horas."),
                progreso=k.pct_sobre_guia,
                delta=ui.delta_pp(k.pct_sobre_guia, k0.pct_sobre_guia) if filtrado else "",
                escala=("0 %", "100 % de los días"))
    with c_kpis:
        nv = niveles(cont)
        ui.kpis([
            dict(rotulo=f"Mediana de {et}", valor=ui.fmt_num(k.mediana), unidad="µg/m³",
                 nota=f"<b>{k.multiplo_guia:.1f}×</b> la guía de {g:g} µg/m³",
                 delta=(f"{'▲' if k.mediana > k0.mediana else '▼'} {abs(k.mediana - k0.mediana):.1f} µg/m³ vs. total"
                        if filtrado and abs(k.mediana - k0.mediana) >= 0.05 else "")),
            dict(rotulo="Sobre la meta IT-1", valor=ui.fmt_pct(k.pct_sobre_it1), unidad="%",
                 nota=f"de los días supera {nv[-1].desde:g} µg/m³, el escalón más laxo de la OMS",
                 color=t.severidad[5],
                 delta=ui.delta_pp(k.pct_sobre_it1, k0.pct_sobre_it1) if filtrado else ""),
            dict(rotulo="Días críticos", valor=ui.fmt_pct(k.pct_criticos), unidad="%",
                 nota="superan a la vez las guías de PM₂.₅, PM₁₀ y NO₂",
                 delta=ui.delta_pp(k.pct_criticos, k0.pct_criticos) if filtrado else ""),
            dict(rotulo="Días limpios", valor=ui.fmt_pct(k.pct_limpios), unidad="%",
                 nota=f"cumplen las tres guías: <b>{round(k.pct_limpios * k.n / 100):,}</b> de {k.n:,} días",
                 color=t.severidad[0],
                 delta=ui.delta_pp(k.pct_limpios, k0.pct_limpios) if filtrado else ""),
        ])

    # --- Dónde: severidad por ciudad + mapa -----------------------------------------------
    resumen = por_ciudad(df_contexto, cont)
    dist = distribucion_niveles(df_contexto, cont)
    seleccion = tuple(f.ciudades)

    c_barras, c_mapa = st.columns([7, 5], gap="medium")
    with c_barras, st.container(key="tarjeta-niveles"):
        ui.titulo_grafico(
            f"Cómo se reparten los días de cada ciudad según la escala OMS de {et}",
            "Ordenadas por la proporción de días sobre IT-1, el tramo más severo. "
            "A la derecha, el % total de días sobre la guía.")
        ui.leyenda_severidad(niveles(cont), t.severidad)
        st.plotly_chart(graficos.barras_niveles(dist, resumen, cont, t, seleccion),
                        key="sel_niveles", on_select=lambda: _al_seleccionar("sel_niveles", 2),
                        selection_mode="points", config=graficos.CONFIG, theme=None)
        ui.nota("Clic en una ciudad para filtrar todo el tablero; clic de nuevo para quitar el filtro.")

    with c_mapa:
        with st.container(key="tarjeta-mapa"):
            ui.titulo_grafico(f"Mediana de {et} por ciudad",
                              "Escala fija de 0 a 2× IT-1: un color parejo significa un problema parejo.")
            st.plotly_chart(graficos.mapa_ciudades(resumen, cont, t, seleccion, alto=330),
                            key="sel_mapa", on_select=lambda: _al_seleccionar("sel_mapa", 8),
                            selection_mode="points", config=graficos.CONFIG, theme=None)
        with st.container(key="tarjeta-lectura"):
            mas, menos = resumen.iloc[0], resumen.iloc[-1]
            brecha = mas["pct_sobre_guia"] - menos["pct_sobre_guia"]
            if len(f.ciudades) == 1 and len(resumen) > 1:
                fila = resumen[resumen["City"] == f.ciudades[0]].iloc[0]
                puesto = int(resumen.index[resumen["City"] == f.ciudades[0]][0]) + 1
                cuerpo = (f"<b>{nombre_ciudad(fila['City'])}</b> ocupa el puesto <b>{puesto} de "
                          f"{len(resumen)}</b> en días sobre la guía ({fila['pct_sobre_guia']:.0f} %). "
                          f"La brecha entre la primera y la última ciudad es de solo {brecha:.0f} puntos: "
                          "su situación es la norma, no la excepción.")
            elif len(resumen) > 1:
                cuerpo = (f"Entre la ciudad más afectada (<b>{nombre_ciudad(mas['City'])}</b>, "
                          f"{mas['pct_sobre_guia']:.0f} %) y la menos afectada "
                          f"(<b>{nombre_ciudad(menos['City'])}</b>, {menos['pct_sobre_guia']:.0f} %) "
                          f"hay apenas <b>{brecha:.0f} puntos</b>. "
                          + ("Ninguna ciudad escapa: el problema no es local, es generalizado."
                             if brecha < 15 else
                             "Hay diferencias marcadas entre ciudades: conviene priorizar."))
            else:
                cuerpo = (f"<b>{nombre_ciudad(mas['City'])}</b> supera la guía el "
                          f"{mas['pct_sobre_guia']:.0f} % de los días, con una mediana de "
                          f"{mas['mediana']:.0f} µg/m³ ({mas['multiplo_guia']:.1f}× la guía).")
            ui.titulo_grafico("Lectura")
            ui.html(f'<p class="sub-graf" style="margin:0">{cuerpo}</p>')

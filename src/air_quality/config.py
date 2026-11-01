"""Constantes compartidas por el pipeline, el notebook y el dashboard."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "global_air_quality_data_messy.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "air_quality_procesado.csv"

RANDOM_STATE = 42

POLL = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]   # contaminantes
METEO = ["Temperature", "Humidity", "Wind Speed"]    # meteorología
NUM = POLL + METEO
CLAVES = ["City", "Country", "Date"]                 # claves de negocio

FORMATO_FECHA = "%m/%d/%Y"

# Guías OMS 2021 para 24 h (µg/m³)
UMBRALES_OMS = {"PM2.5": 15, "PM10": 45, "NO2": 25}

TRIMESTRE = {12: "DEF", 1: "DEF", 2: "DEF", 3: "MAM", 4: "MAM", 5: "MAM",
             6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}

ORDEN_VIENTO = ["muy bajo", "bajo", "medio", "alto"]

DERIVADAS = ["ratio_pm", "n_excedencias_oms", "pm25_vs_ciudad", "pm25_movil_7d",
             "pm25_delta", "mes_sin", "mes_cos", "dia_sem_sin", "dia_sem_cos"]
CONTINUAS = NUM + ["ratio_pm", "n_excedencias_oms", "pm25_vs_ciudad",
                   "pm25_movil_7d", "pm25_delta"]
CODIFICADAS = ["viento_ord", "fin_semana_int", "mes_sin", "mes_cos",
               "dia_sem_sin", "dia_sem_cos"]
# pm25_vs_ciudad: combinación lineal exacta de PM2.5 y las dummies de City.
# viento_ord: duplicado ordinal de Wind Speed.
EXCLUIR_MODELO = ["pm25_vs_ciudad", "viento_ord"]

# Columnas del CSV entregable (data/processed)
ENTREGABLE = CLAVES + NUM + ["ratio_pm", "n_excedencias_oms", "pm25_vs_ciudad",
                             "pm25_movil_7d", "pm25_delta", "mes", "dia_semana",
                             "fin_semana", "trimestre_met"]
# Derivadas que se redondean a la precisión de las mediciones antes de exportar
REDONDEAR = ["ratio_pm", "pm25_vs_ciudad", "pm25_movil_7d", "pm25_delta"]

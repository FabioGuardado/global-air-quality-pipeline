"""Constantes compartidas por el pipeline, el notebook y el dashboard."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "global_air_quality_data_messy.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "air_quality_procesado.csv"

RANDOM_STATE = 42

# Fuente del dataset crudo (se muestra en el dashboard). Pendiente: URL de Kaggle.
FUENTE_NOMBRE = "dataset global de calidad del aire (Kaggle)"
FUENTE_URL = ""

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

# Región y coordenadas (aprox. centro urbano) de cada ciudad normalizada.
REGIONES = ["Norteamérica", "Latinoamérica", "Europa", "África y Medio Oriente", "Asia",
            "Oceanía"]
CIUDADES = {
    "toronto":        ("Norteamérica", 43.65, -79.38),
    "new york":       ("Norteamérica", 40.71, -74.01),
    "los angeles":    ("Norteamérica", 34.05, -118.24),
    "mexico city":    ("Latinoamérica", 19.43, -99.13),
    "rio de janeiro": ("Latinoamérica", -22.91, -43.17),
    "london":         ("Europa", 51.51, -0.13),
    "paris":          ("Europa", 48.86, 2.35),
    "berlin":         ("Europa", 52.52, 13.40),
    "madrid":         ("Europa", 40.42, -3.70),
    "moscow":         ("Europa", 55.76, 37.62),
    "istanbul":       ("Europa", 41.01, 28.98),
    "cairo":          ("África y Medio Oriente", 30.04, 31.24),
    "johannesburg":   ("África y Medio Oriente", -26.20, 28.05),
    "dubai":          ("África y Medio Oriente", 25.20, 55.27),
    "mumbai":         ("Asia", 19.08, 72.88),
    "bangkok":        ("Asia", 13.76, 100.50),
    "beijing":        ("Asia", 39.90, 116.41),
    "seoul":          ("Asia", 37.57, 126.98),
    "tokyo":          ("Asia", 35.68, 139.69),
    "sydney":         ("Oceanía", -33.87, 151.21),
}

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
ENTREGABLE = ["City", "Country", "region", "Date"] + NUM + ["ratio_pm", "n_excedencias_oms", "pm25_vs_ciudad",
                             "pm25_movil_7d", "pm25_delta", "mes", "dia_semana",
                             "fin_semana", "trimestre_met"]
# Derivadas que se redondean a la precisión de las mediciones antes de exportar
REDONDEAR = ["ratio_pm", "pm25_vs_ciudad", "pm25_movil_7d", "pm25_delta"]

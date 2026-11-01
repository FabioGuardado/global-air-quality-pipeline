# Global Air Quality Pipeline

Proyecto de la materia **Data Analysis** (UEES): perfilado, limpieza, análisis exploratorio y
visualización de un dataset global de calidad del aire (PM2.5, PM10, NO2, SO2, CO, O3 y
variables meteorológicas en 20 ciudades).

**Equipo:** F. E. Guardado · D. H. Méndez · A. X. Landaverde · R. E. Escobar

| Fase | Entregable | Estado |
|---|---|---|
| I | Pipeline de limpieza + EDA (`notebooks/`), artículo IEEE (`paper/`) | ✅ |
| II | Dashboard interactivo + adenda IEEE (Sección V-B) | 🚧 en curso |

## Estructura

```
├── data/
│   ├── raw/                 # CSV original (no se modifica)
│   └── processed/           # salida del pipeline, la que consume el dashboard
├── notebooks/
│   └── eda_pipeline.ipynb   # narrativa de las Fases 0-V, importa src/air_quality
├── src/air_quality/         # pipeline, escala OMS, métricas, patrones, hipótesis, escenarios y auditoría
├── app/                     # dashboard de Streamlit (Fase II)
│   ├── streamlit_app.py     # punto de entrada
│   ├── tema.py              # paletas validadas, plantilla Plotly y CSS (claro/oscuro)
│   ├── filtros.py           # filtros globales y filtro cruzado
│   └── capitulos/           # un módulo por capítulo de la narrativa
├── tests/
│   ├── unit/                # cada módulo del paquete, con datos sintéticos
│   ├── integration/         # pipeline completo sobre el dataset real y el notebook
│   └── app/                 # la app con streamlit.testing y los constructores de gráficos
├── paper/                   # artículo IEEE (LaTeX), figuras y PDF compilado
├── pyproject.toml
├── requirements.txt         # ejecución (pipeline, notebook, dashboard)
└── requirements-dev.txt     # + tests y ejecución del notebook
```

## Instalación

Requiere Python 3.11 o superior.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
```

Ambos `requirements` instalan también el paquete `air_quality` en modo editable (`-e .`),
así que el notebook, los tests y el dashboard importan el mismo código.

## Uso

**Dashboard:**

```bash
streamlit run app/streamlit_app.py
```

**Regenerar el dataset procesado** a partir del crudo:

```bash
python -m air_quality.pipeline
# opcional: --entrada ruta/crudo.csv --salida ruta/procesado.csv
```

**Notebook:** abrir `notebooks/eda_pipeline.ipynb` en Jupyter o VS Code y ejecutar todas las
celdas en orden. En la Fase V el notebook comprueba que su resultado coincide con el del paquete.

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/eda_pipeline.ipynb
```

**Tests:**

```bash
pytest                      # todo (incluye el notebook, ~30 s)
pytest -m "not slow"        # sin ejecutar el notebook
pytest tests/unit           # solo unitarios
pytest tests/app            # solo la app
pytest tests/unit/test_derivadas.py::test_delta_reinicia_en_cada_ciudad   # un test
pytest --cov=air_quality    # con cobertura
```

**Artículo:** desde `paper/`, compilar con `pdflatex main.tex` (dos veces para las
referencias). Las figuras se buscan en `paper/figures/`.

## Pipeline

| Fase | Qué hace | Módulo |
|---|---|---|
| I | Copia inmutable, perfilado, normalización de `City`/`Country`, `Date` en `%m/%d/%Y` | `limpieza` |
| II | EDA: distribuciones, correlaciones, estacionalidad, umbrales OMS, fin de semana | notebook |
| III | Duplicados exactos y por clave, imputación por ciudad, outliers (IQR, Z, MAD, Mahalanobis) | `limpieza`, `imputacion`, `outliers` |
| IV | Derivadas → codificación → escalado, control de VIF | `derivadas`, `transformacion` |
| V | Auditoría pre/post y exportación a `data/processed/` | `pipeline` |

Cada decisión queda registrada en una bitácora (`air_quality.bitacora.Bitacora`) con su
justificación.

**Resultado:** de 30,450 filas crudas quedan **5,075 observaciones** únicas
(20 ciudades × días) y 22 columnas sin nulos (incluida la región). El diccionario de datos está al final del
notebook.

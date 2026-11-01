# Análisis Exploratorio y Perfilado desde la Ciencia de Datos de La Calidad del Aire Global

# Resumen / Abstract

**Título:** Análisis Exploratorio y Perfilado desde la Ciencia de Datos de La Calidad del Aire Global

El monitoreo y evaluación de la calidad del aire representa un desafío fundamental para la salud pública y la comprensión del cambio climático [1], [8]. Este proyecto aplica un flujo riguroso de Ciencia de Datos para llevar a cabo el perfilado inicial, la auditoría de calidad y el Análisis Exploratorio de Datos (EDA) sobre un conjunto de datos global de 30,450 observaciones que abarca mediciones de contaminantes atmosféricos ($PM_{2.5}$, $PM_{10}$, $NO_2$, $SO_2$, $CO$, $O_3$) y variables meteorológicas (temperatura, humedad y velocidad del viento). La metodología comprende la implementación de una copia inmutable del dataset, la depuración de redundancias y la imputación fundamentada de faltantes, así como el análisis probabilístico univariado y multivariado [4], [6]. 

**Resultados y hallazgos clave:**
* **Sanamiento y preservación de varianza:** Se identificó y depuró un **34.47% de duplicidad masiva (10,495 registros)**, logrando recuperar un conjunto continuo de 19,955 observaciones con **0.00% de outliers extremales** fuera de los límites de Tukey [4] y una retención de varianza estocástica superior al **99.50%**.
* **Cumplimiento crítico de guías de la OMS:** Más del **93.17% de los días monitoreados superan el umbral diario de $PM_{2.5}$** de la OMS [1], seguido de un **82.92% para $PM_{10}$** y un **79.34% para $NO_2$**.
* **Inexistencia del "efecto fin de semana":** Las pruebas no paramétricas de Mann-Whitney U confirmaron que las concentraciones de $NO_2$, $CO$ y $PM_{2.5}$ no varían significativamente entre días laborales y fines de semana ($p > 0.18$), demostrando emisiones continuas e ininterrumpidas.
* **Independencia meteorológica:** Se observó una correlación muy débil entre factores climáticos y contaminantes ($|r_s| < 0.03$), así como entre $PM_{2.5}$ y $PM_{10}$ ($r = 0.018$).

**Conclusión:**
Este estudio proporciona un diagnóstico integral del estado de los datos, demostrando que la contaminación ambiental global responde a patrones antropogénicos de fondo y preparando un dataset depurado y confiable para su posterior modelado predictivo.

**Palabras clave:** Ciencia de Datos, Calidad del Aire, Análisis Exploratorio de Datos (EDA), Perfilado de Datos, Contaminantes Atmosféricos, OMS.

# Introducción

La contaminación del aire constituye uno de los mayores desafíos ambientales y de salud pública a nivel global en el siglo XXI. De acuerdo con la Organización Mundial de la Salud (OMS), la exposición a material particulado en suspensión ($PM_{2.5}$ y $PM_{10}$) y a gases contaminantes como el dióxido de nitrógeno ($NO_2$), dióxido de azufre ($SO_2$), monóxido de carbono ($CO$) y ozono troposférico ($O_3$) está directamente asociada con el incremento en la morbilidad y mortalidad por enfermedades cardiovasculares y respiratorias [1]. Diversas investigaciones en entornos urbanos regionales resaltan la urgente necesidad de caracterizar la exposición a estos agentes patógenos en poblaciones expuestas a alta densidad vehicular e industrial [8]. Asimismo, la dinámica de dispersión, concentración y transformación química de estos contaminantes atmosféricos se encuentra intrínsecamente ligada a variables meteorológicas fundamentales como la temperatura, la humedad relativa y la velocidad del viento.

A pesar de la creciente disponibilidad de redes de monitoreo ambiental y sensores remotos, las bases de datos observacionales sobre calidad del aire con frecuencia sufren de problemas estructurales, tales como valores faltantes, inconsistencias de formato, registros duplicados, presencia de ruido y valores atípicos (*outliers*) derivados de fallas de calibración o discontinuidades en la recolección de datos [6], [9]. La presencia de estas anomalías sin un tratamiento riguroso compromete la validez de los análisis estadísticos y reduce la precisión de eventuales modelos predictivos de calidad del aire.

En este contexto, las metodologías de la Ciencia de Datos ofrecen un marco analítico idóneo para auditar y caracterizar la integridad de los datos ambientales antes de su modelado. Este trabajo aborda el **Análisis Exploratorio y Perfilado desde la Ciencia de Datos de la Calidad del Aire Global**, con el objetivo de evaluar la estructura, calidad y distribuciones probabilísticas de un conjunto de datos multivariable e interdisciplinario. 

Para alcanzar dicho objetivo, el estudio contempla:
1. La implementación de un flujo de ingesta reproducible mediante el uso de copias inmutables de los datos brutos.
2. Un perfilado sistemático de calidad de datos enfocado en el diagnóstico de tipos de datos, patrones de ausencia (datos faltantes) e inconsistencias dimensionales.
3. Un Análisis Exploratorio de Datos (EDA) univariado y multivariado para identificar comportamientos distribucionales, valores atípicos y correlaciones entre parámetros contaminantes y factores meteorológicos [4].

A través de este enfoque metódico, se busca sentar las bases para la depuración y estandarización de conjuntos de datos ambientales, garantizando la trazabilidad del proceso y la generación de insumos de alta calidad para la toma de decisiones informadas y la investigación atmosférica.

# II. Descripción del Dataset y Diagnóstico Inicial

## A. Origen y Procedencia de los Datos
El conjunto de datos analizado (`global_air_quality_data_messy.csv`) registra mediciones de calidad del aire y parámetros meteorológicos a escala global. La masa de datos cuenta con una dimensión total de **30,450 observaciones (filas)** y **12 atributos (columnas)**. El dataset captura lecturas distribuidas en 120 ciudades pertenecientes a 19 países, abarcando concentraciones de contaminantes atmosféricos clave e indicadores climáticos. Para la manipulación, inspección de tipos y estructuración tabular de estas variables se utilizó la biblioteca fundamental pandas [2]. Con el fin de evaluar técnicas de auditoría de datos en escenarios reales, el conjunto presenta duplicidad masiva de registros, discontinuidades y valores faltantes concentrados en las variables contaminantes.

## B. Diccionario Formal de Variables
La Tabla I sintetiza la estructura técnica, tipo de dato detectado por el intérprete, dominio teórico y unidades de medida de las variables presentes en el dataset.

### Tabla I: Diccionario de variables del dataset de calidad del aire
| Variable | Tipo de Dato (Pandas) | Dominio / Unidades | Descripción |
| :--- | :--- | :--- | :--- |
| **City** | `object` (Texto) | Nominal / 120 ciudades | Ciudad de localización de la estación de monitoreo. |
| **Country** | `object` (Texto) | Nominal / 19 países | País donde se realiza la medición. |
| **Date** | `object` (Texto) | Fecha / `M/D/YYYY` | Fecha correspondiente a la lectura ambiental. |
| **PM2.5** | `float64` | Continuous / $\mu g/m^3$ | Concentración de material particulado $\le 2.5\,\mu m$. |
| **PM10** | `float64` | Continuous / $\mu g/m^3$ | Concentración de material particulado $\le 10\,\mu m$. |
| **NO2** | `float64` | Continuous / $ppb$ | Concentración de Dióxido de Nitrógeno. |
| **SO2** | `float64` | Continuous / $ppb$ | Concentración de Dióxido de Azufre. |
| **CO** | `float64` | Continuous / $ppm$ | Concentración de Monóxido de Carbono. |
| **O3** | `float64` | Continuous / $ppb$ | Concentración de Ozono troposférico. |
| **Temperature**| `float64` | Continuous / $^\circ C$ | Temperatura ambiente (Rango: $-10.00^\circ C$ a $40.00^\circ C$). |
| **Humidity** | `float64` | Continuous / $\%$ | Humedad relativa del aire (Rango: $10.01\%$ a $99.99\%$). |
| **Wind Speed** | `float64` | Continuous / $m/s$ | Velocidad del viento en superficie (Rango: $0.50$ a $20.00\,m/s$). |

---

## C. Matriz Diagnóstica de Calidad Inicial (Perfilado de Datos)
El diagnóstico de integridad sobre el dataset crudo arrojó los siguientes hallazgos cuantitativos:

1. **Duplicidad Masiva:** Se detectaron **10,495 filas duplicadas exactas**, lo que representa un **34.47% de redundancia** sobre el total de la base de datos (30,450 filas).
2. **Coerción de Tipos de Datos:** La variable `Date` fue leída erróneamente como tipo `object` (cadena de texto) debido al formato de almacenamiento (`M/D/YYYY`), requiriendo conversión explícita a tipo `datetime64`.
3. **Ausencia de Datos (Missing Values):** Las variables meteorológicas (`Temperature`, `Humidity`, `Wind Speed`) y geográficas (`City`, `Country`, `Date`) no presentan valores nulos ($0.00\%$). Sin embargo, todas las variables de contaminantes atmosféricos registran un patrón sistemático de datos faltantes que oscila entre el $4.84\%$ y el $5.25\%$:
   * **$O_3$**: 1,600 nulos ($5.25\%$)
   * **$NO_2$**: 1,593 nulos ($5.23\%$)
   * **$PM_{10}$**: 1,561 nulos ($5.13\%$)
   * **$PM_{2.5}$**: 1,552 nulos ($5.10\%$)
   * **$CO$**: 1,496 nulos ($4.91\%$)
   * **$SO_2$**: 1,475 nulos ($4.84\%$)

### Tabla II: Matriz diagnóstica de calidad de datos inicial
| Columna | Tipo de Dato | Registros Totales | Valores Nulos | % Ausencia | Valores Únicos |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **City** | `object` | 30,450 | 0 | 0.00% | 120 |
| **Country** | `object` | 30,450 | 0 | 0.00% | 19 |
| **Date** | `object` | 30,450 | 0 | 0.00% | 336 |
| **PM2.5** | `float64` | 30,450 | 1,552 | 5.10% | 6,915 |
| **PM10** | `float64` | 30,450 | 1,561 | 5.13% | 7,407 |
| **NO2** | `float64` | 30,450 | 1,593 | 5.23% | 5,951 |
| **SO2** | `float64` | 30,450 | 1,475 | 4.84% | 4,190 |
| **CO** | `float64` | 30,450 | 1,496 | 4.91% | 991 |
| **O3** | `float64` | 30,450 | 1,600 | 5.25% | 7,387 |
| **Temperature**| `float64` | 30,450 | 0 | 0.00% | 4,254 |
| **Humidity** | `float64` | 30,450 | 0 | 0.00% | 5,811 |
| **Wind Speed** | `float64` | 30,450 | 0 | 0.00% | 1,940 |

# III. Metodología de Preprocesamiento y Transformación

Para garantizarlos principios de reproducibilidad e integridad analítica en el pipeline de Ciencia de Datos, el preprocesamiento se diseñó mediante una secuencia ordenada de operaciones algebraicas y estadísticas. Cada técnica aplicada responde a las propiedades distribucionales observadas en el diagnóstico inicial.

---

## A. Prevención Rigurosa de Fuga de Datos
La fuga de datos (*data leakage*) ocurre cuando información proveniente del conjunto de evaluación/prueba o del universo global distorsiona los parámetros de transformación durante la fase de entrenamiento o procesamiento. Para evitar este sesgo:
1. **Desacoplamiento Estricto:** La limpieza primaria (eliminación de duplicados exactos y estandarización tipográfica) se realiza de manera inmutable.
2. **Aislamiento de Estadísticos:** La estimación de parámetros para la imputación de faltantes ($\mu$, $\tilde{x}$) y para los escaladores numéricos ($\mu$, $\sigma$, $x_{min}$, $x_{max}$) se calcula estrictamente sobre el conjunto de entrenamiento (*Fit*), para posteriormente aplicar dicha transformación (*Transform*) sobre los conjuntos de validación o prueba mediante el ecosistema scikit-learn [3].

---

## B. Saneamiento de Redundancia y Corrección de Tipos
El primer paso operativo consistió en la depuración de duplicados exactos mediante la función de equidad multidimensional sobre el vector de atributos $\mathbf{x}_i$:

$$\mathbf{x}_i = \mathbf{x}_j \iff x_{i,k} = x_{j,k} \quad \forall k \in \{1, 2, \dots, K\}$$

Al remover las observaciones redundantes, el volumen de datos se redujo de $N = 30,450$ a $N = 19,955$ registros únicos (eliminando $10,495$ observaciones superfluas, equivalentes al $34.47\%$ de redundancia). Posteriormente, el atributo `Date` fue parseado del dominio numérico-textual al estándar ISO-8601 (`YYYY-MM-DD`).

---

## C. Detección Cuantitativa de Outliers e Invarianza de Dispersión
Para evaluar la presencia de valores atípicos se empleó el criterio del Rango Intercuartílico ($IQR$), definido como la diferencia entre el tercer cuartil ($Q_3$ o percentil 75) y el primer cuartil ($Q_1$ o percentil 25):

$$IQR = Q_3 - Q_1$$

Los límites de aceptación para la detección de anomalías se establecen mediante las fronteras de Tukey:

$$\text{Límite Inferior} = Q_1 - 1.5 \times IQR$$
$$\text{Límite Superior} = Q_3 + 1.5 \times IQR$$

Un valor $x_{i,k}$ se clasifica formalmente como valor atípico si cumple la condición:

$$x_{i,k} < (Q_1 - 1.5 \times IQR) \quad \lor \quad x_{i,k} > (Q_3 + 1.5 \times IQR)$$

Complementariamente, para el análisis de estimadores robustos de dispersión alternativos al desvío estándar tradicional se consideran las métricas de varianza acotada [5].

**Resultados del Diagnóstico de Outliers:** 
El análisis probabilístico reveló que todas las variables numéricas continúan dentro de distribuciones acotadas y simétricas (coeficientes de asimetría o *skewness* $\vert{}\gamma_1\vert{} < 0.02$). Los rangos observados para $PM_{2.5}$ ($[5.02, 149.98]\,\mu g/m^3$) y $PM_{10}$ ($[10.00, 200.00]\,\mu g/m^3$) responden a cotas físicas reales de sensores, registrando **0.00% de outliers extremales** fuera de las fronteras de Tukey. Por tanto, no se aplicó truncamiento (*winsorization*) ni eliminación arbitraria de observaciones atípicas.

---

## D. Fundamentación Teórica e Imputación de Valores Faltantes
Tras la remoción de duplicados, las variables de contaminantes presentaron una tasa de ausencia uniforme ($\sim 7.11\%$ a $7.68\%$). La prueba de asimetría de Fisher-Pearson dio como resultado un valor cercano a cero ($\gamma_1 \approx 0.00$) para todos los contaminantes:

$$\gamma_1 = \frac{\frac{1}{n} \sum_{i=1}^{n} (x_i - \bar{x})^3}{\left( \frac{1}{n} \sum_{i=1}^{n} (x_i - \bar{x})^2 \right)^{3/2}} \approx 0$$

Al confirmarse la simetría mesocúrtica de las variables y un patrón de ausencia completamente al azar (MCAR - *Missing Completely at Random*), se justificó formalmente la imputación por la Media Condicional o Media Global ($\bar{x}_k$):

$$\bar{x}_k = \frac{1}{\vert{}S_k\vert{}} \sum_{i \in S_k} x_{i,k}$$

donde $S_k = \{i \mid x_{i,k} \text{ no es nulo}\}$. 

Para variables categóricas o agrupamientos por ciudad ($c$), la imputación estratificada se define como:

$$\hat{x}_{i,k}^{(c)} = \frac{1}{\vert{}S_{k,c}\vert{}} \sum_{j \in S_{k,c}} x_{j,k}$$

---

## E. Normalización y Escalado Numérico
Dado que las variables del dataset poseen diferentes magnitudes y unidades de medida ($\mu g/m^3$, $ppb$, $ppm$, $^\circ C$, $\%$, $m/s$), se estructuraron dos formulaciones matemáticas de escalado implementadas en módulos de preprocesamiento [3]:

### 1. Z-Score / StandardScaler (Estandarización)
Apta para algoritmos basados en distancias euclidianas o gradientes que asumen distribuciones gaussianas. Transforma la variable para obtener media $\mu = 0$ y desviación estándar $\sigma = 1$:

$$z_{i,k} = \frac{x_{i,k} - \mu_k}{\sigma_k}$$

donde:
$$\mu_k = \frac{1}{N} \sum_{i=1}^{N} x_{i,k}, \quad \sigma_k = \sqrt{\frac{1}{N-1} \sum_{i=1}^{N} (x_{i,k} - \mu_k)^2}$$

### 2. Min-Max Scaler (Escalado Acotado)
Acota los atributos en el intervalo cerrado $[0, 1]$, ideal para redes neuronales o modelos donde se requiere preservar exactamente las relaciones de magnitud cero:

$$x'_{i,k} = \frac{x_{i,k} - \min(X_k)}{\max(X_k) - \min(X_k)}$$

---

## F. Codificación Categórica e Ingeniería de Características
1. **One-Hot Encoding (Variables Categóricas Nominales):**
   Las variables `City` (120 categorías) y `Country` (19 categorías) son nominales sin orden intrínseco [6]. La transformación genera $M$ vectores binarios ficticios (*dummy variables*):

   $$y_{i,m} = \begin{cases} 1 & \text{si el registro } i \text{ pertenece a la categoría } m \\ 0 & \text{en otro caso} \end{cases}$$

   Para evitar la multicolinealidad perfecta o "trampa de las variables ficticias" en modelos lineales, se omite una categoría de referencia ($M - 1$).

2. **Ingeniería de Características Derivadas (Descomposición Temporal y Ratios):**
   * **Descomposición de Fecha:** A partir de $Date \rightarrow (Año, Mes, Día, Día\_Semana)$.
   * **Ratio Particulado ($R_{PM}$):** Proporción física entre finas y gruesas:

     $$R_{PM} = \frac{PM_{2.5}}{PM_{10}} \quad (R_{PM} \in [0, 1])$$

# IV. Resultados Experimentales & Discusión

## A. Evidencia Cuantitativa Pre y Post Procesamiento

### 1. Preservación de Varianza vs. Eliminación de Redundancia
El impacto del tratamiento de datos se evaluó comparando la estructura de dispersión antes y después de la depuración. La remoción masiva de las **10,495 observaciones duplicadas (34.47% de redundancia)** permitió eliminar el sesgo de sobremuestreo sin erosionar la variabilidad estocástica real del fenómeno ambiental. 

Como se observa en la métrica de varianza retenida ($\sigma^2_{\text{post}} / \sigma^2_{\text{pre}}$), el pipeline de preprocesamiento logró retener más del **99.50% de la varianza original** en todas las variables de contaminantes ($PM_{2.5}: 99.92\%$, $PM_{10}: 99.75\%$, $NO_2: 99.50\%$, $O_3: 99.55\%$). Esto confirma que la depuración eliminó el ruido y la inflación de grados de libertad sin alterar las propiedades probabilísticas del conjunto de datos.

> **[INSERTAR AQUÍ: FIGURA 1 — Diagramas de caja (Boxplots) y gráficos de densidad (KDE) comparativos pre vs. post procesamiento para PM2.5 y PM10]**

### 2. Estructura de Asimetría y Correlación
Las mediciones numéricas mantuvieron coeficientes de asimetría de Fisher-Pearson cercanos a cero ($|\gamma_1| < 0.02$), confirmando distribuciones mesocúrticas y acotadas. Las matrices de correlación de Pearson y Spearman post-procesamiento se generaron utilizando la biblioteca de visualización estadística seaborn [7], reflejando la ausencia de distorsiones provocadas por valores espurios o duplicación artificial de registros.

> **[INSERTAR AQUÍ: FIGURA 2 — Matriz de correlación multivariable (Heatmap de Pearson y Spearman) post-procesamiento]**

---

## B. Discusión de Preguntas Analíticas de Investigación

A continuación se presentan las respuestas fundamentadas a las siete preguntas de investigación planteadas en la Fase II:

### 1. ¿Cómo evoluciona la contaminación en el tiempo?
* **Resultado Cuantitativo:** Durante el periodo registrado (año 2023), los promedios globales observados para los principales contaminantes se mantuvieron estables: $PM_{2.5}$ en $77.72\,\mu g/m^3$, $PM_{10}$ en $104.26\,\mu g/m^3$, $NO_2$ en $52.09\,ppb$, $SO_2$ en $25.18\,ppb$, $CO$ en $5.04\,ppm$ y $O_3$ en $105.44\,ppb$.
* **Discusión:** La serie temporal no muestra tendencias drásticas de alza o baja a escala agregada global, lo que indica que la variabilidad depende principalmente de factores locales o estacionales específicos por región geográfica en lugar de un choque global uniforme.

> **[INSERTAR AQUÍ: FIGURA 3 — Gráfico de líneas sobre la evolución mensual promedio de PM2.5 para las ciudades principales]**

---

### 2. ¿Existe estacionalidad, y es igual en todas las ciudades?
* **Resultado Cuantitativo:** El análisis por pivote de calor (*heatmap*) normalizado por ciudad revela variaciones en los picos mensuales de $PM_{2.5}$. Las diferencias entre los meses de mayor concentración reflejan el contraste hemisférico entre el Norte y el Sur.
* **Discusión:** La hipótesis se confirma: la estacionalidad del material particulado está acoplada a los patrones dinámicos locales (e.g., épocas secas/lluviosas e inversión térmica invernal), variando el mes crítico según la ubicación geográfica de cada metrópoli.

> **[INSERTAR AQUÍ: FIGURA 4 — Mapas de calor (Heatmaps) de estacionalidad mensual de PM2.5 normalizados por ciudad]**

---

### 3. ¿Difieren los niveles entre ciudades y países?
* **Resultado Cuantitativo:** La prueba no paramétrica de Kruskal-Wallis sobre las distribuciones de $PM_{2.5}$ entre ciudades arrojó un valor $p = 0.244$ ($p > 0.05$).
* **Discusión:** A diferencia de lo presupuestado en la hipótesis inicial, no se detectó una diferencia estadísticamente significativa en las medianas de $PM_{2.5}$ entre las distintas ciudades al evaluarse de forma agregada. Esto demuestra que en este dataset las fluctuaciones de contaminación presentan magnitudes homogéneamente elevadas a lo largo de las distintas estaciones de monitoreo.

> **[INSERTAR AQUÍ: FIGURA 5 — Diagrama de cajas (Boxplots) ordenado de PM2.5 por ciudad]**

---

### 4. ¿Cómo influyen las variables meteorológicas?
* **Resultado Cuantitativo:** La matriz de correlación de Spearman entre contaminantes y factores meteorológicos arrojó coeficientes de asociación muy débiles:
  * Temperatura vs $PM_{2.5}$ ($r_s = -0.022$) y $O_3$ ($r_s = 0.008$).
  * Velocidad del viento vs $PM_{2.5}$ ($r_s = 0.005$) y $O_3$ ($r_s = -0.017$).
* **Discusión:** Los datos no muestran una dispersión eólica significativa ni una fotólisis impulsada por temperatura a nivel macro. Esto sugiere que las variaciones climáticas locales registradas en la muestra actúan como moduladores de segundo orden frente a las fuentes de emisión antropogénicas directas.

> **[INSERTAR AQUÍ: FIGURA 6 — Diagramas de dispersión (Scatterplots) y boxplots categorizados por velocidad del viento vs PM2.5]**

---

### 5. ¿Qué contaminantes se mueven juntos?
* **Resultado Cuantitativo:** La correlación lineal de Pearson entre $PM_{2.5}$ y $PM_{10}$ resultó baja ($r = 0.018$), al igual que la relación entre $NO_2$ y $CO$ ($r = 0.007$).
* **Discusión:** Se rechaza la hipótesis de una alta colinealidad entre el material particulado fino y grueso en esta base de datos. La independencia observada entre las especies químicas sugiere dinámicas de emisión dispares o una recolección de sensores con calibraciones independientes para cada parámetro contaminante.

> **[INSERTAR AQUÍ: FIGURA 7 — Gráfico de dispersión (Scatterplot) entre PM10 y PM2.5 con ajuste de regresión]**

---

### 6. ¿Con qué frecuencia se superan los umbrales de la OMS?
* **Resultado Cuantitativo:** Al evaluar los límites diarios de la OMS [1], se encontró un porcentaje alarmante de días en incumplimiento:
  * **$PM_{2.5}$ ($> 15\,\mu g/m^3$):** Se supera en el **$93.17\%$** de los días analizados.
  * **$PM_{10}$ ($> 45\,\mu g/m^3$):** Se supera en el **$82.92\%$** de los días.
  * **$NO_2$ ($> 25\,ppb$):** Se supera en el **$79.34\%$** de los días.
* **Discusión:** Este es el hallazgo de mayor impacto del proyecto: la inmensa mayoría de las ciudades monitoreadas registran niveles de contaminación que exceden sistemáticamente los estándares de salud pública internacional [1] [8], subrayando la urgencia de intervenciones regulatorias.

> **[INSERTAR AQUÍ: FIGURA 8 — Gráfico de barras del porcentaje de días que exceden las guías de la OMS por ciudad]**

---

### 7. ¿Cambia el patrón entre días laborales y fines de semana?
* **Resultado Cuantitativo:** La prueba de rangos con signo de Mann-Whitney U no mostró diferencias significativas entre días laborales y fines de semana:
  * **$NO_2$:** Mediana laboral = $51.82$, fin de semana = $52.92$ ($p = 0.502$).
  * **$CO$:** Mediana laboral = $5.08$, fin de semana = $5.07$ ($p = 0.675$).
  * **$PM_{2.5}$:** Mediana laboral = $78.63$, fin de semana = $78.08$ ($p = 0.185$).
* **Discusión:** Se refuta la hipótesis de un "efecto fin de semana", es decir, una disminución de emisiones por reducción de tráfico. Las emisiones industriales o de transporte de fondo permanecen constantes a lo largo de toda la semana en las ciudades de la muestra.

# V. Conclusiones y Trabajo Futuro

## A. Síntesis del Impacto del Pipeline en la Calidad del Dataset
La ejecución del flujo metodológico de ingeniería de datos sobre el dataset `global_air_quality_data_messy.csv` transformó una masa de datos cruda y degradada en un insumo analítico útil, garantizando la trazabilidad y reproducibilidad del proceso [6]. 

1. **Saneamiento Dimensional:** La eliminación de **10,495 registros duplicados exactos** depuró un **34.47% de redundancia**, corrigiendo la sobreestimación del peso estadístico de observaciones repetidas y reduciendo la carga computacional en procesos posteriores.
2. **Preservación Estructural de la Varianza:** La imputación de datos faltantes en las variables de contaminantes ($\sim 7.11\%$ a $7.68\%$ de ausencias por imputación de media/mediana condicional) permitió recuperar un conjunto de datos continuo y completo [9], reteniendo más del **99.50% de la varianza estocástica original** y corrigiendo la asimetría probabilística sin introducir sesgo de distorsión.
3. **Estandarización de Dominio:** La coerción explícita de tipos de datos (notablemente el formateo de `Date` a estándar ISO-8601) y la codificación de variables categóricas sientan las bases para la ingesta directa por parte de algoritmos de aprendizaje automático (*Machine Learning*) y plataformas de Inteligencia de Negocios (*Business Intelligence*) [3].

---

## B. Conclusiones sobre los Hallazgos

1. **Estado Crítico de Exposición Global:** El hallazgo de mayor trascendencia revela que más del **93.17% de los días analizados superan los umbrales de $PM_{2.5}$** establecidos por las Guías de Calidad del Aire de la OMS [1], seguidos por un **82.92% para $PM_{10}$** y un **79.34% para $NO_2$**.
2. **Inexistencia de "Efecto Fin de Semana":** La prueba no paramétrica de Mann-Whitney U confirmó que no existen diferencias estadísticamente significativas ($p > 0.18$) en las concentraciones de $NO_2$, $CO$ y $PM_{2.5}$ entre días laborales y fines de semana. Las fuentes de emisión industrial y urbana de fondo permanecen constantes de forma ininterrumpida.
3. **Independencia Dinámica de Contaminantes y Meteorología:** Contrario a los supuestos teóricos tradicionales, las correlaciones entre contaminantes y factores climáticos locales (temperatura, humedad, velocidad del viento) mostraron coeficientes de asociación muy débiles ($\vert{}r_s\vert{} < 0.03$), así como una baja colinealidad lineal entre $PM_{2.5}$ y $PM_{10}$ ($r = 0.018$). Esto refleja que la variabilidad atmosférica en este dataset está dominada por factores antropogénicos directos o patrones microclimáticos acoplados regionalmente.

---

## C. Limitaciones Metodológicas Identificadas

1. **Granularidad Temporal Agregada:** El dataset proporciona lecturas con frecuencia diaria, lo que impide analizar fenómenos intradía críticos, como los picos de tráfico vehicular en horas punta o la dinámica fotoquímica diurna/nocturna del ozono ($O_3$).
2. **Heterogeneidad en la Densidad de Sensores:** Aunque el dataset incluye 120 ciudades de 19 países, no se dispone de metadatos sobre la ubicación micro-topográfica de las estaciones, por ejemplo, distancia a vías de alto tráfico, zonas industriales o parques urbanos, lo que puede generar sesgos de representatividad espacial.
3. **Imputación Univariada de Faltantes:** Aunque la imputación por la media condicional preservó la simetría de las distribuciones, para series de tiempo complejas este método puede suavizar artificialmente picos extremos puntuales [9].

---

## D. Recomendaciones para Modelos Futuros de Machine Learning y BI

1. **Ingeniería de Características de Rezagos Temporales *Lags*:** Para el entrenamiento de modelos predictivos de series de tiempo e.g., ARIMA, XGBoost o LSTM, se recomienda incorporar variables desfasadas ($t-1$, $t-7$) y ventanas móviles de promedios *Rolling Means* para capturar la memoria interna de los contaminantes en la atmósfera.
2. **Uso de Imputación Multivariada Avance MICE o KNN Imputer:** Para fases predictivas en producción, se sugiere reemplazar la imputación por la media por métodos de Imputación Múltiple por Ecuaciones Encadenadas (MICE) o vecinos más cercanos (KNN), explotando las dependencias estocásticas locales entre estaciones vecinas mediante scikit-learn [3].
3. **Escalado Robusto:** Al entrenar algoritmos sensibles a la magnitud e.g., Regresión Ridge/Lasso, Redes Neuronales o SVM, se debe utilizar `StandardScaler` o `RobustScaler` [5] ajustando los parámetros únicamente sobre la partición de entrenamiento (*Train Fold*) para evitar la fuga de datos, el *data leakage*.
4. **Despliegue de Tableros de BI:** Se recomienda integrar este pipeline procesado en motores de inteligencia de negocios, por ejemplo, Power BI o Tableau estructurando un modelo en estrella *Star Schema*, donde la tabla de hechos contenga las mediciones normalizadas y las dimensiones permitan el filtrado geográfico (`Country`, `City`) y temporal (`Year`, `Month`, `DayOfWeek`).

---

## E. Recomendaciones desde la Perspectiva de Salud Pública

1. **Rediseño de Alertas Tempranas Ambientales:** Dado que más del $90\%$ de los días sobrepasan los límites de la OMS para $PM_{2.5}$, las autoridades sanitarias no deben limitar las alertas a "episodios críticos excepcionales", sino estructurar programas permanentes de mitigación de riesgo para poblaciones vulnerables como niños, adultos mayores y pacientes con afecciones respiratorias o cardiovasculares [8].
2. **Políticas Continuas de Control de Emisiones:** Al confirmarse la ausencia de una disminución de contaminantes durante los fines de semana, las normativas ambientales deben enfocarse en la regulación continua de fuentes fijas industriales y en la transición hacia transporte público con reducción de emisiones u otros medios de transporte individual con cero emisiones, en lugar de restricciones de tráfico exclusivamente orientadas a días hábiles.
3. **Fortalecimiento de la Red de Monitoreo Comunitario:** Se recomienda complementar las estaciones oficiales de calidad del aire con redes de sensores de bajo costo distribuidas estratégicamente, permitiendo validar la exposición real a nivel de vecindario e informar intervenciones de planificación urbana [8], por ejemplo, la  creación de barreras de vegetación y zonas de bajas emisiones normadas en las ordenanzas.

# Referencias

[1] World Health Organization, *WHO global air quality guidelines: particulate matter (PM2.5 and PM10), ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide*, Geneva, Switzerland: World Health Organization, 2021.

[2] W. McKinney, "Data Structures for Statistical Computing in Python," in *Proceedings of the 9th Python in Science Conference (SciPy 2010)*, Austin, TX, USA, 2010, pp. 56–61.

[3] F. Pedregosa *et al.*, "Scikit-learn: Machine Learning in Python," *Journal of Machine Learning Research*, vol. 12, pp. 2825–2830, 2011.

[4] J. W. Tukey, *Exploratory Data Analysis*, Reading, MA, USA: Addison-Wesley, 1977.

[5] P. J. Rousseeuw and C. Croux, "Alternatives to the Median Absolute Deviation," *Journal of the American Statistical Association*, vol. 88, no. 424, pp. 1273–1283, 1993.

[6] H. Wickham, "Tidy Data," *Journal of Statistical Software*, vol. 59, no. 10, pp. 1–23, 2014.

[7] M. Waskom, "seaborn: statistical data visualization," *Journal of Open Source Software*, vol. 6, no. 60, p. 3021, 2021.

[8] D. L. L. Rivas y E. A. M. Portillo, "Evaluación de la calidad del aire y su impacto en la salud de poblaciones urbanas," Tesis de Grado, Facultad de Ciencias de la Salud, Universidad Evangélica de El Salvador (UEES), San Salvador, El Salvador, 2022. Disponible en Biblioteca Virtual UEES.

[9] R. J. A. Little and D. B. Rubin, *Statistical Analysis with Missing Data*, 3rd ed., Hoboken, NJ, USA: John Wiley & Sons, 2019.
# Corte 3 · Semana 14 — Análisis temporal y visualización

Actividad calificable del Corte 3. Se analiza una serie temporal de ventas diarias de una cafetería: se agrega por periodo con `resample`, se calcula una media móvil, se describe la tendencia y la estacionalidad, se construyen dos gráficos y se optimiza una consulta SQL (más dos medidas DAX).

## Contenido de la carpeta

```
semana-14/
├── README.md
├── requirements.txt
├── generar_datos.py        # crea el CSV de ventas (simulado, semilla fija)
├── analisis_temporal.py    # resample, media móvil, estacionalidad y gráficos
├── datos/
│   ├── ventas_diarias.csv      # 3 288 filas: fecha, categoria, ventas_cop
│   ├── resumen_mensual.csv     # mensual + medias móviles
│   └── indice_estacional.csv
├── img/
│   ├── 01_evolucion_ventas.png
│   └── 02_comparacion_trimestres.png
├── sql/
│   ├── consulta_optimizada.sql
│   └── probar_consulta.py      # mide plan de ejecución y tiempos
└── dax/
    └── medidas.dax
```

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
python generar_datos.py          # solo si se quiere regenerar el CSV
python analisis_temporal.py      # imprime resultados y guarda los gráficos
python sql/probar_consulta.py    # compara la consulta original y la optimizada
```

## Datos

Serie de ventas diarias de una cafetería, del 1 de enero de 2023 al 31 de diciembre de 2025 (1 096 días), separada en tres categorías: Bebidas, Panadería y Granos. Los valores están en pesos colombianos (COP). Los datos son **simulados** (con tendencia, estacionalidad anual y efecto del día de la semana) para poder practicar el análisis; el script `generar_datos.py` los reproduce con una semilla fija.

## Metodología

1. Se suman las categorías para tener la venta total por día.
2. `resample` a semana (`W`), mes (`MS`), trimestre (`QS`) y año (`YS`): 158 semanas, 36 meses, 12 trimestres y 3 años.
3. Media móvil de 3 meses (suaviza el ruido de corto plazo) y de 12 meses. Con la media móvil centrada 2x12 se obtiene la tendencia sin estacionalidad.
4. Estacionalidad: se divide la venta mensual entre la tendencia y se promedia por mes del año; el resultado se normaliza para que el promedio sea 1,00 (un índice de 1,35 significa 35 % por encima de la tendencia).

### Tendencia

| Año | Ventas (millones COP) | Crecimiento |
|---|---|---|
| 2023 | 469,2 | — |
| 2024 | 519,2 | +10,7 % |
| 2025 | 579,3 | +11,6 % |

El crecimiento anual compuesto es de 11,1 %. La tendencia centrada pasa de 39,2 millones de COP al mes (julio de 2023) a 48,0 (junio de 2025), es decir, sube cerca de 0,38 millones cada mes. La media centrada pierde seis meses en cada extremo de la serie, por eso no cubre de enero de 2023 a diciembre de 2025.

### Estacionalidad

| Mes | Índice | Mes | Índice |
|---|---|---|---|
| Enero | 0,86 | Julio | 1,11 |
| Febrero | **0,83** | Agosto | 0,97 |
| Marzo | 0,96 | Septiembre | 0,92 |
| Abril | 0,93 | Octubre | 0,98 |
| Mayo | 1,00 | Noviembre | 1,05 |
| Junio | 1,04 | Diciembre | **1,35** |

El mes más fuerte es diciembre en los tres años y el más débil es febrero. Hay un segundo repunte en junio–julio (vacaciones de mitad de año) y un arranque de año flojo en enero–febrero. También hay un patrón semanal: el sábado vende 19 % por encima del promedio diario y el martes 12 % por debajo.

## Visualizaciones

### 1. Evolución: las ventas crecen y repiten el pico de diciembre

![Evolución de las ventas mensuales](img/01_evolucion_ventas.png)

Línea gris con la venta mensual y línea azul con la media móvil de 3 meses. El eje vertical parte de cero para que la altura sea proporcional al valor. La media móvil recorta los picos de diciembre y deja ver el avance sostenido.

### 2. Comparación: el cuarto trimestre es el más fuerte, año tras año

![Ventas por trimestre y año](img/02_comparacion_trimestres.png)

Barras agrupadas por trimestre, una por año, en una rampa de un solo tono (más oscuro = año más reciente). El eje parte de cero. El cuarto trimestre concentra en promedio 29,2 % de las ventas del año, frente a 21,1 % del primero.

## Optimización SQL

La consulta pide el total mensual por categoría de 2025. La versión original aplicaba `strftime` sobre la columna `fecha` en el `WHERE` (lo que impide usar un índice) y calculaba el total con una subconsulta correlacionada que recorría toda la tabla una vez por grupo. La versión optimizada usa un filtro por rango de fechas y un solo `SUM ... GROUP BY`, apoyado en un índice cubriente `(fecha, categoria, ventas_cop)`.

| Versión | Plan de ejecución | Tiempo |
|---|---|---|
| Original | `SCAN v` + `SCAN v2` por cada grupo | ≈ 40,5 ms |
| Reescrita, sin índice | `SCAN ventas` | ≈ 0,39 ms |
| Reescrita + índice | `SEARCH ... USING COVERING INDEX` | ≈ 0,31 ms |

Las tres devuelven exactamente las mismas 36 filas. Casi toda la mejora viene de reescribir la consulta; el índice cambia el plan de recorrido completo a búsqueda por rango y su efecto aumenta cuando la tabla acumula más historia. Los tiempos dependen del equipo. El código completo y los comentarios están en `sql/consulta_optimizada.sql`.

## Medidas DAX

En `dax/medidas.dax` hay dos medidas para el indicador de ventas:

- **Ventas Media Movil 3M**: promedio de los últimos tres meses con `DATESINPERIOD`; devuelve vacío cuando no hay tres meses completos, igual que la media móvil de pandas.
- **Crecimiento Anual %**: compara el periodo actual con el mismo periodo del año anterior usando `SAMEPERIODLASTYEAR`; debe dar 10,7 % en 2024 y 11,6 % en 2025, igual que en Python.

## Findings

Monthly sales of the café grew from about 39 million COP in mid-2023 to about 48 million COP in mid-2025, once seasonality is removed with a centered 12-month moving average. Yearly totals rose 10.7% in 2024 and 11.6% in 2025, which gives a compound growth rate of roughly 11% per year. The series has a strong annual seasonality: December is the peak in all three years, with a seasonal index of 1.35 (about 35% above trend), while February is the weakest month at 0.83, and there is a smaller bump in June and July. The first chart shows the monthly sales in gray and the 3-month moving average in blue; the moving average smooths the sharp December spikes and makes the steady upward trend easier to see. The second chart compares quarterly sales for each year side by side, and it shows that the fourth quarter holds about 29% of annual sales and that every quarter beats the same quarter of the previous year. Both charts start the vertical axis at zero, so the bar and line heights are proportional to the real values. Finally, the data are simulated and cover only three years, so each monthly seasonal index rests on two or three observations and should be read as an illustration of the method rather than a firm forecast.

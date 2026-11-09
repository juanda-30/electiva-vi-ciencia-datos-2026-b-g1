"""
Genera datos/ventas_diarias.csv

Ventas diarias (en pesos colombianos) de una cafetería pequeña, 2023-2025,
separadas en tres categorías. Los datos son simulados con semilla fija para que
el resultado sea reproducible. Si se tiene una serie real, basta con reemplazar
el CSV respetando las columnas: fecha, categoria, ventas_cop.
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

fechas = pd.date_range("2023-01-01", "2025-12-31", freq="D")

# multiplicador por mes (el pico de diciembre y el bache de enero-febrero)
estacional = {1: 0.88, 2: 0.90, 3: 0.97, 4: 0.96, 5: 1.00, 6: 1.06,
              7: 1.10, 8: 0.99, 9: 0.95, 10: 1.00, 11: 1.08, 12: 1.30}
# multiplicador por día de la semana (lunes = 0)
semanal = [0.92, 0.90, 0.94, 0.98, 1.10, 1.22, 1.14]
# participación de cada categoría en la venta total
categorias = {"Bebidas": 0.55, "Panadería": 0.30, "Granos": 0.15}

base_diaria = 1_150_000      # venta diaria promedio al arrancar 2023 (COP)
crecimiento_anual = 0.11     # tendencia de fondo

filas = []
for dia in fechas:
    anios = (dia - fechas[0]).days / 365
    tendencia = base_diaria * (1 + crecimiento_anual) ** anios
    factor = estacional[dia.month] * semanal[dia.dayofweek]
    for cat, peso in categorias.items():
        extra = 1.0
        if cat == "Granos" and dia.month == 12:
            extra = 1.25     # el café en grano se vende como regalo de fin de año
        if cat == "Bebidas" and dia.month in (6, 7):
            extra = 1.05     # vacaciones de mitad de año
        ruido = rng.lognormal(0, 0.07)
        valor = tendencia * peso * factor * extra * ruido
        filas.append((dia.strftime("%Y-%m-%d"), cat, int(round(valor, -2))))

df = pd.DataFrame(filas, columns=["fecha", "categoria", "ventas_cop"])

salida = Path(__file__).resolve().parent / "datos" / "ventas_diarias.csv"
salida.parent.mkdir(exist_ok=True)
df.to_csv(salida, index=False, encoding="utf-8")
print(f"{len(df)} filas guardadas en {salida}")

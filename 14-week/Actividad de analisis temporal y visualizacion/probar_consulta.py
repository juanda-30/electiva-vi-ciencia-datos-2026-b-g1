"""
Compara la consulta original contra la optimizada (SQLite).

Carga datos/ventas_diarias.csv en una base en memoria, revisa el plan de
ejecución (EXPLAIN QUERY PLAN), mide el tiempo y comprueba que las dos
consultas devuelvan exactamente lo mismo.
"""
import sqlite3
import time
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE / "datos" / "ventas_diarias.csv")

con = sqlite3.connect(":memory:")
df.to_sql("ventas", con, index=False)

ANTES = """
SELECT strftime('%Y-%m', v.fecha) AS mes,
       v.categoria,
       (SELECT SUM(v2.ventas_cop)
          FROM ventas v2
         WHERE strftime('%Y-%m', v2.fecha) = strftime('%Y-%m', v.fecha)
           AND v2.categoria = v.categoria) AS total_cop
FROM ventas v
WHERE strftime('%Y', v.fecha) = '2025'
GROUP BY mes, v.categoria
ORDER BY mes, v.categoria;
"""

DESPUES = """
SELECT substr(fecha, 1, 7) AS mes,
       categoria,
       SUM(ventas_cop) AS total_cop
FROM ventas
WHERE fecha >= '2025-01-01' AND fecha < '2026-01-01'
GROUP BY mes, categoria
ORDER BY mes, categoria;
"""

INDICE = "CREATE INDEX idx_ventas_fecha_cat ON ventas (fecha, categoria, ventas_cop);"


def plan(sql):
    return [fila[3] for fila in con.execute("EXPLAIN QUERY PLAN " + sql)]


def medir(sql, repeticiones=7):
    mejor = None
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        filas = con.execute(sql).fetchall()
        dt = (time.perf_counter() - t0) * 1000
        mejor = dt if mejor is None else min(mejor, dt)
    return mejor, filas


print(f"Filas en la tabla: {len(df)}\n")

print("--- ANTES (sin índice) ---")
for p in plan(ANTES):
    print("  ", p)
t_antes, res_antes = medir(ANTES)
print(f"   mejor tiempo: {t_antes:.2f} ms\n")

print("--- DESPUÉS, solo reescribiendo la consulta (sin índice) ---")
for p in plan(DESPUES):
    print("  ", p)
t_sin_idx, res_sin_idx = medir(DESPUES)
print(f"   mejor tiempo: {t_sin_idx:.2f} ms\n")

con.execute(INDICE)
print("--- DESPUÉS, reescrita + índice cubriente ---")
for p in plan(DESPUES):
    print("  ", p)
t_despues, res_despues = medir(DESPUES)
print(f"   mejor tiempo: {t_despues:.2f} ms\n")

print("Mismo resultado antes/después:", res_antes == res_despues == res_sin_idx)
print("Filas devueltas:", len(res_despues))
print(f"Mejora: {t_antes / t_despues:.0f}x más rápida que la original")
print("\nPrimeras filas:")
for fila in res_despues[:4]:
    print("  ", fila)

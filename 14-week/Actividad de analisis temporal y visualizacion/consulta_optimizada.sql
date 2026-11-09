-- ============================================================
-- Semana 14 - Optimización de una consulta
-- Indicador: ventas mensuales por categoría en 2025 (tabla ventas)
-- Motor probado: SQLite (ver sql/probar_consulta.py)
-- ============================================================

-- ------------------------------------------------------------
-- VERSIÓN ORIGINAL (lenta)
-- ------------------------------------------------------------
-- Problemas:
--  1) strftime('%Y', fecha) = '2025' aplica una función a la columna fecha
--     en el WHERE; por eso ningún índice sobre fecha se puede usar.
--  2) La subconsulta correlacionada se ejecuta una vez por cada grupo
--     (mes, categoría) y en cada ejecución vuelve a recorrer TODA la tabla
--     calculando strftime fila por fila.
--  3) El total se podía obtener con un solo SUM + GROUP BY.
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

-- ------------------------------------------------------------
-- VERSIÓN OPTIMIZADA
-- ------------------------------------------------------------
-- Cambios:
--  1) Filtro por rango (fecha >= ... AND fecha < ...): deja la columna "limpia"
--     para poder usar un índice.
--  2) Una sola pasada con SUM + GROUP BY en lugar de la subconsulta.
--  3) substr(fecha, 1, 7) para sacar 'AAAA-MM' (el formato ISO ya lo permite).
SELECT substr(fecha, 1, 7) AS mes,
       categoria,
       SUM(ventas_cop)     AS total_cop
FROM ventas
WHERE fecha >= '2025-01-01'
  AND fecha <  '2026-01-01'
GROUP BY mes, categoria
ORDER BY mes, categoria;

-- Índice cubriente: contiene las tres columnas que usa la consulta, así el
-- motor responde solo con el índice y no necesita leer la tabla.
CREATE INDEX idx_ventas_fecha_cat
    ON ventas (fecha, categoria, ventas_cop);

-- ------------------------------------------------------------
-- RESULTADOS MEDIDOS (3 288 filas, mejor de 7 ejecuciones, mi equipo)
-- ------------------------------------------------------------
--  Versión                              Plan de ejecución                       Tiempo
--  Original                             SCAN v + SCAN v2 por cada grupo         ~40.5 ms
--  Reescrita, sin índice                SCAN ventas                             ~0.39 ms
--  Reescrita + índice cubriente         SEARCH ... USING COVERING INDEX         ~0.31 ms
--
-- Las tres devuelven exactamente las mismas 36 filas (12 meses x 3 categorías).
-- Casi toda la mejora (~100x) viene de reescribir la consulta; el índice cambia
-- el plan de SCAN a SEARCH y su efecto crece a medida que la tabla tiene más
-- años de historia. Los tiempos dependen de la máquina; lo importante es el plan.
--
-- Nota: la misma idea aplica en SQL Server o PostgreSQL (evitar YEAR(fecha) = 2025
-- en el WHERE y usar un rango de fechas).

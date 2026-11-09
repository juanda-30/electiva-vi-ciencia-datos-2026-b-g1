"""
Corte 3 - Semana 14: análisis temporal y visualización

Serie: ventas diarias de una cafetería (COP), 2023-2025.
Pasos:
  1. cargar y sumar las categorías por día
  2. resample a semana, mes y trimestre
  3. media móvil (3 y 12 meses) y tendencia
  4. estacionalidad (índice estacional por mes)
  5. dos gráficos: evolución y comparación
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
RUTA_DATOS = BASE / "datos" / "ventas_diarias.csv"
CARPETA_IMG = BASE / "img"
CARPETA_IMG.mkdir(exist_ok=True)

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MES_CORTO = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep",
             "oct", "nov", "dic"]
ORDINAL = {1: "primer", 2: "segundo", 3: "tercer", 4: "cuarto"}
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

# ---------------------------------------------------------------- 1. datos
df = pd.read_csv(RUTA_DATOS, parse_dates=["fecha"])
diaria = df.groupby("fecha")["ventas_cop"].sum().sort_index()

# ------------------------------------------------------------- 2. resample
semanal = diaria.resample("W").sum()       # semanas que terminan en domingo
mensual = diaria.resample("MS").sum()
trimestral = diaria.resample("QS").sum()
anual = diaria.resample("YS").sum()

# ------------------------------------------------------ 3. media móvil
ma3 = mensual.rolling(3).mean()
ma12 = mensual.rolling(12).mean()
# media móvil centrada 2x12: sirve para quitar la estacionalidad y ver la tendencia
tendencia = mensual.rolling(12).mean().rolling(2).mean().shift(-6)

crec_anual = anual.pct_change().dropna() * 100
cagr = ((anual.iloc[-1] / anual.iloc[0]) ** (1 / (len(anual) - 1)) - 1) * 100
t = tendencia.dropna()
pendiente, _ = np.polyfit(np.arange(len(t)), t.values, 1)

# --------------------------------------------------------- 4. estacionalidad
razon = mensual / tendencia                       # ventas reales / tendencia
indice = razon.groupby(razon.index.month).mean()
indice = indice / indice.mean()                   # promedio = 1.0
mes_pico = int(indice.idxmax())
mes_valle = int(indice.idxmin())

# ¿el mes más fuerte de cada año es siempre el mismo?
pico_por_anio = mensual.groupby(mensual.index.year).idxmax().dt.month
pico_constante = pico_por_anio.nunique() == 1

# patrón semanal (día de la semana vs. promedio general)
por_dia = diaria.groupby(diaria.index.dayofweek).mean()
indice_dia = por_dia / por_dia.mean()

# ------------------------------------------------------ guardar resúmenes
resumen = pd.DataFrame({
    "ventas_cop": mensual,
    "media_movil_3m": ma3.round(0),
    "media_movil_12m": ma12.round(0),
    "tendencia_centrada": tendencia.round(0),
})
resumen.index.name = "mes"
resumen.to_csv(BASE / "datos" / "resumen_mensual.csv", encoding="utf-8")

est = pd.DataFrame({"mes": MESES, "indice_estacional": indice.round(3).values})
est.to_csv(BASE / "datos" / "indice_estacional.csv", index=False, encoding="utf-8")

# ------------------------------------------------------------- 5. gráficos
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
APAGADO = "#898781"
REJILLA = "#e1e0d9"
EJE = "#c3c2b7"
AZUL = "#2a78d6"
RAMPA_ANIOS = {2023: "#86b6ef", 2024: "#2a78d6", 2025: "#104281"}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.facecolor": SUPERFICIE,
    "axes.facecolor": SUPERFICIE,
    "axes.edgecolor": EJE,
    "axes.labelcolor": TINTA_2,
    "xtick.color": APAGADO,
    "ytick.color": APAGADO,
    "text.color": TINTA,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.axisbelow": True,
})


def estilo_ejes(ax):
    ax.grid(axis="y", color=REJILLA, linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)


def encabezado(fig, titulo, subtitulo):
    fig.text(0.015, 0.955, titulo, fontsize=14.5, fontweight="bold",
             ha="left", va="top", color=TINTA)
    fig.text(0.015, 0.895, subtitulo, fontsize=10.5, ha="left", va="top",
             color=TINTA_2)


def pie(fig, texto):
    fig.text(0.015, 0.015, texto, fontsize=8.5, ha="left", va="bottom",
             color=APAGADO)


# ---- Gráfico 1: evolución (línea) -------------------------------------
if pico_constante:
    frase_pico = f"tocan su pico cada {MESES[mes_pico - 1]}"
else:
    frase_pico = f"son más fuertes en {MESES[mes_pico - 1]}"
titulo1 = f"Las ventas crecen ~{cagr:.0f}% al año y {frase_pico}"

mens_m = mensual / 1e6
ma3_m = ma3 / 1e6

fig, ax = plt.subplots(figsize=(10, 5.6))
fig.subplots_adjust(top=0.80, left=0.085, right=0.88, bottom=0.14)
ax.plot(mens_m.index, mens_m.values, color=APAGADO, linewidth=1.4,
        label="Ventas mensuales")
ax.plot(ma3_m.index, ma3_m.values, color=AZUL, linewidth=2.6,
        label="Media móvil de 3 meses")
ax.set_ylim(0, mens_m.max() * 1.15)
ax.set_xlim(mens_m.index[0] - pd.Timedelta(days=20),
            mens_m.index[-1] + pd.Timedelta(days=75))

marcas = [d for d in mens_m.index if d.month in (1, 7)]
ax.set_xticks(marcas)
ax.set_xticklabels([f"{MES_CORTO[d.month - 1]} {d.year}" for d in marcas])
ax.set_ylabel("Ventas mensuales (millones de COP)")
estilo_ejes(ax)

# etiquetas directas al final de cada línea
ax.text(mens_m.index[-1] + pd.Timedelta(days=12), ma3_m.iloc[-1] - 2,
        "Media móvil\n3 meses", fontsize=9, color=TINTA_2, va="center")
f_max = mens_m.idxmax()
ax.text(mens_m.index[-1] + pd.Timedelta(days=12), mens_m.iloc[-1],
        f"Mensual\n({MES_CORTO[f_max.month - 1]} {f_max.year}: {mens_m.max():.0f})",
        fontsize=9, color=TINTA_2, va="center")

# anotar solo un pico de diciembre para señalar la estacionalidad
dic_2023 = pd.Timestamp("2023-12-01")
ax.annotate("Pico de diciembre\n(se repite cada año)",
            xy=(dic_2023, mens_m[dic_2023]),
            xytext=(dic_2023 - pd.Timedelta(days=150), mens_m.max() * 0.97),
            fontsize=9, color=TINTA_2, ha="center",
            arrowprops=dict(arrowstyle="-", color=APAGADO, lw=0.9))
ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=TINTA_2)

encabezado(fig, titulo1,
           "Ventas mensuales de la cafetería, enero 2023 – diciembre 2025 · el eje vertical parte de cero")
pie(fig, "Datos simulados para el ejercicio · la media móvil promedia el mes y los dos anteriores")
fig.savefig(CARPETA_IMG / "01_evolucion_ventas.png", dpi=200)
plt.close(fig)

# ---- Gráfico 2: comparación (barras agrupadas por trimestre) ----------
tri = trimestral.to_frame("v")
tri["anio"] = tri.index.year
tri["q"] = tri.index.quarter
pv = (tri.pivot(index="q", columns="anio", values="v") / 1e6)

participacion = (pv / pv.sum() * 100).mean(axis=1)
q_top = int(participacion.idxmax())
crece_siempre = bool((pv.diff(axis=1).iloc[:, 1:] > 0).all().all())
if crece_siempre:
    cola = "y cada año supera al anterior"
else:
    cola = "aunque el crecimiento anual no es parejo"
titulo2 = (f"El {ORDINAL[q_top]} trimestre concentra ~{participacion[q_top]:.0f}% "
           f"de las ventas {cola}")

fig, ax = plt.subplots(figsize=(10, 5.6))
fig.subplots_adjust(top=0.80, left=0.085, right=0.97, bottom=0.16)
ancho = 0.26
x = np.arange(4)
for i, anio in enumerate(pv.columns):
    barras = ax.bar(x + (i - 1) * ancho, pv[anio].values, width=ancho,
                    color=RAMPA_ANIOS[anio], edgecolor=SUPERFICIE,
                    linewidth=1.6, label=str(anio))
    if anio == pv.columns[-1]:
        for b, v in zip(barras, pv[anio].values):
            ax.text(b.get_x() + b.get_width() / 2, v + pv.values.max() * 0.012,
                    f"{v:.0f}", ha="center", va="bottom", fontsize=9,
                    color=TINTA_2)
ax.set_ylim(0, pv.values.max() * 1.15)
ax.set_xticks(x)
ax.set_xticklabels(["T1\nene–mar", "T2\nabr–jun", "T3\njul–sep", "T4\noct–dic"])
ax.set_ylabel("Ventas del trimestre (millones de COP)")
estilo_ejes(ax)
leyenda = ax.legend(title="Año", loc="upper left", frameon=True, fontsize=9,
                    title_fontsize=9, labelcolor=TINTA_2, facecolor=SUPERFICIE,
                    edgecolor=SUPERFICIE, framealpha=1)
leyenda.get_title().set_color(TINTA_2)

encabezado(fig, titulo2,
           "Ventas por trimestre y año · el eje vertical parte de cero · cifras sobre las barras de 2025")
pie(fig, "Datos simulados para el ejercicio")
fig.savefig(CARPETA_IMG / "02_comparacion_trimestres.png", dpi=200)
plt.close(fig)

# --------------------------------------------------------------- salida
print("=== Totales anuales (millones de COP) ===")
print((anual / 1e6).round(1).rename(lambda d: d.year).to_string())
print("\nCrecimiento interanual (%):")
print(crec_anual.round(1).rename(lambda d: d.year).to_string())
print(f"Crecimiento anual compuesto 2023-2025: {cagr:.1f}%")
print(f"Pendiente de la tendencia: {pendiente / 1e6:.2f} millones de COP por mes")
print(f"Tendencia centrada: {t.iloc[0] / 1e6:.1f} -> {t.iloc[-1] / 1e6:.1f} millones/mes")

print("\n=== Índice estacional por mes (1.00 = promedio) ===")
for m in range(1, 13):
    print(f"{MESES[m - 1]:<11} {indice[m]:.3f}")
print(f"Mes pico: {MESES[mes_pico - 1]} ({indice[mes_pico]:.2f}) | "
      f"mes valle: {MESES[mes_valle - 1]} ({indice[mes_valle]:.2f})")
print(f"Pico por año: {[MESES[m - 1] for m in pico_por_anio]} | constante: {pico_constante}")

print("\n=== Patrón semanal (1.00 = promedio) ===")
for d in range(7):
    print(f"{DIAS[d]:<10} {indice_dia[d]:.3f}")

print("\n=== Trimestres (millones de COP) ===")
print(pv.round(1).to_string())
print("\nParticipación media por trimestre (%):")
print(participacion.round(1).to_string())
print(f"Cada trimestre supera al del año anterior: {crece_siempre}")

print(f"\nMáximo mensual: {mens_m.max():.1f} millones en {f_max:%Y-%m}")
print(f"Filas diarias: {len(diaria)} | semanas: {len(semanal)} | meses: {len(mensual)} | trimestres: {len(trimestral)}")
print("\nTítulo 1:", titulo1)
print("Título 2:", titulo2)

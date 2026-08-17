"""
==========================================
TEST CLASIFICACIÓN - Explorar las 8 hojas
==========================================
Objetivo: Ver la estructura del Excel y entender
qué información hay en cada hoja.
"""

import pandas as pd

# ==========================================
# CONFIGURACIÓN
# ==========================================
RUTA_CLASIFICACION = "data/clasificacion_2024.xlsx"

print("=" * 70)
print("EXPLORANDO EL EXCEL DE CLASIFICACIÓN")
print("=" * 70)

# ==========================================
# 1. LISTAR TODAS LAS HOJAS
# ==========================================
excel_file = pd.ExcelFile(RUTA_CLASIFICACION)
hojas = excel_file.sheet_names

print(f"\nHojas encontradas: {len(hojas)}")
for i, hoja in enumerate(hojas, 1):
    print(f"   {i}. '{hoja}'")

# ==========================================
# 2. INSPECCIONAR CADA HOJA
# ==========================================
print(f"\n{'=' * 70}")
print("CONTENIDO DE CADA HOJA:")
print(f"{'=' * 70}")

for hoja in hojas:
    print(f"\n{'─' * 70}")
    print(f"  Hoja: '{hoja}'")
    print(f"{'─' * 70}")

    # Leer la hoja
    df = pd.read_excel(RUTA_CLASIFICACION, sheet_name=hoja)

    # Info básica
    print(f"   Dimensiones: {df.shape[0]} filas × {df.shape[1]} columnas")
    print(f"   Columnas: {df.columns.tolist()[:5]}")  # Primeras 5

    # Primeras 3 filas de las 2 primeras columnas
    print(f"\n   Primeras 3 filas (col A y B):")
    print(df.iloc[:3, :2].to_string(index=False))

print(f"\n{'=' * 70}")
print("EXPLORACIÓN COMPLETADA")
print(f"{'=' * 70}")
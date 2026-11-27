"""
test clasificacion - explorar las 8 hojas
objetivo: ver la estructura del Excel y entender
que informacion hay en cada hoja
"""

import pandas as pd

# configuracion
RUTA_CLASIFICACION = "data/clasificacion_2024.xlsx"

print("=" * 70)
print("explorando el excel de clasificacion")
print("=" * 70)

# listar todas las hojas
excel_file = pd.ExcelFile(RUTA_CLASIFICACION)
hojas = excel_file.sheet_names

print(f"\nHojas encontradas: {len(hojas)}")
for i, hoja in enumerate(hojas, 1):
    print(f"   {i}. '{hoja}'")

# inspeccionar cada hoja
print(f"\n{'=' * 70}")
print("contenido de cada hoja:")
print(f"{'=' * 70}")

for hoja in hojas:
    print(f"\n{'─' * 70}")
    print(f"  Hoja: '{hoja}'")
    print(f"{'─' * 70}")

    # leer la hoja
    df = pd.read_excel(RUTA_CLASIFICACION, sheet_name=hoja)

    # info basica
    print(f"   Dimensiones: {df.shape[0]} filas × {df.shape[1]} columnas")
    print(f"   Columnas: {df.columns.tolist()[:5]}")  # primeras 5

    # primeras 3 filas de las 2 primeras columnas
    print(f"\n   Primeras 3 filas (col A y B):")
    print(df.iloc[:3, :2].to_string(index=False))

print(f"\n{'=' * 70}")
print("exploracion completada")
print(f"{'=' * 70}")
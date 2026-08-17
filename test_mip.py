"""
==========================================
TEST MIP - Versión 3.1: LIMPIEZA + BÚSQUEDA
==========================================
Objetivo: Dado un código SCIAN, encontrar:
- TOP 5 clientes (a quién le vende)
- TOP 5 proveedores (de quién compra)

Ajuste: Limpiar espacios extra en los conceptos.
"""

import pandas as pd
import re

# ==========================================
# CONFIGURACIÓN
# ==========================================
RUTA_MIP = "data/MIP_2013.xlsx"
FILA_ENCABEZADOS = 4
SECTOR_A_ANALIZAR = "3111"
TOP_N = 5

print("=" * 60)
print(f"🔍 ANÁLISIS DEL SECTOR: {SECTOR_A_ANALIZAR}")
print("=" * 60)

# ==========================================
# CARGAR LA MIP
# ==========================================
df = pd.read_excel(RUTA_MIP, header=FILA_ENCABEZADOS)

# ==========================================
# LIMPIEZA #1: Eliminar filas basura
# ==========================================
df = df[df["Concepto"].notna()]
df = df[~df["Concepto"].str.startswith("Fuente:", na=False)]

# ==========================================
# LIMPIEZA #2: Quitar espacios extra al inicio/final
# ==========================================
# .str.strip() aplica strip() a cada celda de la columna
df["Concepto"] = df["Concepto"].str.strip()

# También limpiar los nombres de las columnas
df.columns = [str(col).strip() for col in df.columns]

print(f"\n📊 Sectores válidos (después de limpieza): {len(df)}")

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def buscar_columna_por_codigo(df, codigo):
    """Busca la columna que empieza con el código dado."""
    for col in df.columns:
        if str(col).startswith(f"{codigo} "):
            return col
    return None


def buscar_fila_por_codigo(df, codigo):
    """Busca la fila (concepto) que empieza con el código dado."""
    for concepto in df["Concepto"]:
        if str(concepto).startswith(f"{codigo} "):
            return concepto
    return None


# ==========================================
# BÚSQUEDA DEL SECTOR
# ==========================================
nombre_columna = buscar_columna_por_codigo(df, SECTOR_A_ANALIZAR)
nombre_fila = buscar_fila_por_codigo(df, SECTOR_A_ANALIZAR)

if not nombre_columna or not nombre_fila:
    print(f"\n❌ ERROR: No se encontró el sector {SECTOR_A_ANALIZAR}")
    print(f"   Columna encontrada: {nombre_columna}")
    print(f"   Fila encontrada: {nombre_fila}")
    exit()

print(f"\n📌 Sector encontrado:")
print(f"   → {nombre_fila}")

# ==========================================
# TOP CLIENTES (mirar la FILA del sector)
# ==========================================
print(f"\n{'─' * 60}")
print(f"📈 TOP {TOP_N} CLIENTES (a quién le vende {SECTOR_A_ANALIZAR}):")
print(f"{'─' * 60}")

fila_sector = df[df["Concepto"] == nombre_fila].iloc[0]
fila_valores = fila_sector.drop("Concepto")
fila_valores = pd.to_numeric(fila_valores, errors="coerce")

# ⭐ NUEVO: Filtrar solo columnas de sectores REALES
# Crear un DataFrame temporal para poder filtrar por nombre de columna
temp_clientes = pd.DataFrame({
    "sector": fila_valores.index,
    "coeficiente": fila_valores.values
})
temp_clientes = temp_clientes[temp_clientes["sector"].str.match(r"^\d")]

top_clientes = temp_clientes.sort_values("coeficiente", ascending=False).head(TOP_N)

for i, (idx, row) in enumerate(top_clientes.iterrows(), 1):
    porcentaje = row["coeficiente"] * 100
    print(f"\n   {i}. {row['sector']}")
    print(f"      → Coeficiente: {row['coeficiente']:.6f} ({porcentaje:.2f}%)")

# ==========================================
# TOP PROVEEDORES (mirar la COLUMNA del sector)
# ==========================================
print(f"\n{'─' * 60}")
print(f"📉 TOP {TOP_N} PROVEEDORES (de quién compra {SECTOR_A_ANALIZAR}):")
print(f"{'─' * 60}")

columna_valores = df[nombre_columna]
columna_valores = pd.to_numeric(columna_valores, errors="coerce")

temp = pd.DataFrame({
    "sector": df["Concepto"].values,
    "coeficiente": columna_valores.values
})

# ⭐ NUEVO: Filtrar solo sectores REALES (que empiecen con dígito)
# Esto elimina P.1, UEION, IEI, B.1bV, etc.
temp = temp[temp["sector"].str.match(r"^\d")]

top_proveedores = temp.sort_values("coeficiente", ascending=False).head(TOP_N)

for i, (idx, row) in enumerate(top_proveedores.iterrows(), 1):
    porcentaje = row["coeficiente"] * 100
    print(f"\n   {i}. {row['sector']}")
    print(f"      → Coeficiente: {row['coeficiente']:.6f} ({porcentaje:.2f}%)")

print(f"\n{'=' * 60}")
print("✅ ANÁLISIS COMPLETADO")
print(f"{'=' * 60}")
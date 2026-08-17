"""
==========================================
TEST MIP v2 - Función Reutilizable
==========================================
Objetivo: Convertir la lógica en una función
que reciba cualquier código SCIAN.
"""

import pandas as pd
import json

# ==========================================
# CONFIGURACIÓN GLOBAL
# ==========================================
RUTA_MIP = "data/MIP_2013.xlsx"
FILA_ENCABEZADOS = 4
TOP_N = 5


# ==========================================
# FUNCIÓN PRINCIPAL: analizar_sector
# ==========================================
def analizar_sector(codigo_scian, top_n=5):
    """
    Analiza un sector económico según su código SCIAN.
    
    Args:
        codigo_scian (str): Código SCIAN del sector (ej: "3111")
        top_n (int): Cantidad de clientes/proveedores a devolver
    
    Returns:
        dict: Diccionario con la información del sector y sus relaciones
        None: Si el sector no se encuentra
    """
    # ---------- 1. CARGAR Y LIMPIAR LA MIP ----------
    df = pd.read_excel(RUTA_MIP, header=FILA_ENCABEZADOS)
    df = df[df["Concepto"].notna()]
    df = df[~df["Concepto"].str.startswith("Fuente:", na=False)]
    df["Concepto"] = df["Concepto"].str.strip()
    df.columns = [str(col).strip() for col in df.columns]

    # ---------- 2. BUSCAR EL SECTOR ----------
    nombre_columna = None
    for col in df.columns:
        if str(col).startswith(f"{codigo_scian} "):
            nombre_columna = col
            break

    nombre_fila = None
    for concepto in df["Concepto"]:
        if str(concepto).startswith(f"{codigo_scian} "):
            nombre_fila = concepto
            break

    if not nombre_columna or not nombre_fila:
        print(f"Sector '{codigo_scian}' no encontrado")
        return None

    # ---------- 3. OBTENER CLIENTES (fila) ----------
    fila_sector = df[df["Concepto"] == nombre_fila].iloc[0]
    fila_valores = fila_sector.drop("Concepto")
    fila_valores = pd.to_numeric(fila_valores, errors="coerce")

    temp_clientes = pd.DataFrame({
        "sector": fila_valores.index,
        "coeficiente": fila_valores.values
    })
    temp_clientes = temp_clientes[temp_clientes["sector"].str.match(r"^\d")]
    top_clientes = temp_clientes.sort_values("coeficiente", ascending=False).head(top_n)

    # Convertir a lista de diccionarios
    lista_clientes = []
    for _, row in top_clientes.iterrows():
        lista_clientes.append({
            "sector": row["sector"],
            "coeficiente": round(float(row["coeficiente"]), 6),
            "porcentaje": round(float(row["coeficiente"]) * 100, 2)
        })

    # ---------- 4. OBTENER PROVEEDORES (columna) ----------
    columna_valores = pd.to_numeric(df[nombre_columna], errors="coerce")
    temp_proveedores = pd.DataFrame({
        "sector": df["Concepto"].values,
        "coeficiente": columna_valores.values
    })
    temp_proveedores = temp_proveedores[temp_proveedores["sector"].str.match(r"^\d")]
    top_proveedores = temp_proveedores.sort_values("coeficiente", ascending=False).head(top_n)

    # Convertir a lista de diccionarios
    lista_proveedores = []
    for _, row in top_proveedores.iterrows():
        lista_proveedores.append({
            "sector": row["sector"],
            "coeficiente": round(float(row["coeficiente"]), 6),
            "porcentaje": round(float(row["coeficiente"]) * 100, 2)
        })

    # ---------- 5. DEVOLVER RESULTADO ----------
    return {
        "codigo": codigo_scian,
        "sector": nombre_fila,
        "top_clientes": lista_clientes,
        "top_proveedores": lista_proveedores
    }


# ==========================================
# FUNCIÓN AUXILIAR: mostrar_resultado (bonito)
# ==========================================
def mostrar_resultado(resultado):
    """Imprime el resultado de forma bonita en la terminal."""
    if not resultado:
        return

    print(f"\n{'=' * 60}")
    print(f"SECTOR: {resultado['sector']}")
    print(f"{'=' * 60}")

    print(f"\nTOP {len(resultado['top_clientes'])} CLIENTES:")
    for i, cliente in enumerate(resultado['top_clientes'], 1):
        print(f"   {i}. {cliente['sector']}")
        print(f"      → {cliente['porcentaje']}%")

    print(f"\nTOP {len(resultado['top_proveedores'])} PROVEEDORES:")
    for i, proveedor in enumerate(resultado['top_proveedores'], 1):
        print(f"   {i}. {proveedor['sector']}")
        print(f"      → {proveedor['porcentaje']}%")


# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================
if __name__ == "__main__":
    print("=" * 60)
    print("ANÁLISIS DE MÚLTIPLES SECTORES")
    print("=" * 60)

    # Probar con 3 sectores diferentes
    sectores_a_probar = ["3111", "3113", "5241"]

    # NUEVO: Guardar todos los resultados en una lista
    todos_los_resultados = []

    for codigo in sectores_a_probar:
        resultado = analizar_sector(codigo)
        mostrar_resultado(resultado)
        
        if resultado:
            todos_los_resultados.append(resultado)

    # NUEVO: Guardar en archivo JSON
    ruta_salida = "resultados.json"
    
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(todos_los_resultados, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"ANÁLISIS COMPLETADO")
    print(f"Resultados guardados en: {ruta_salida}")
    print(f"   Total de sectores analizados: {len(todos_los_resultados)}")
    print(f"{'=' * 60}")
"""

test mip v2 - Funcion reutilizable

objetivo: convertir la logica en una funcion
que reciba cualquier codigo SCIAN.
"""

import pandas as pd
import json

# configuracion global
RUTA_MIP = "data/MIP_2013.xlsx"
FILA_ENCABEZADOS = 4
TOP_N = 5

# funcion principal: analizar_sector
def analizar_sector(codigo_scian, top_n=5):
    """
    analiza un sector economico segun su codigo SCIAN.
    
    Args:
        codigo_scian (str): codigo SCIAN del sector (ej: "3111")
        top_n (int): cantidad de clientes/proveedores a devolver
    
    Returns:
        dict: diccionario con la información del sector y sus relaciones
        None: si el sector no se encuentra
    """
    #  cargar y limpiar la mip
    df = pd.read_excel(RUTA_MIP, header=FILA_ENCABEZADOS)
    df = df[df["Concepto"].notna()]
    df = df[~df["Concepto"].str.startswith("Fuente:", na=False)]
    df["Concepto"] = df["Concepto"].str.strip()
    df.columns = [str(col).strip() for col in df.columns]

    # buscar el sector
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

    # obtener clientes (fila)
    fila_sector = df[df["Concepto"] == nombre_fila].iloc[0]
    fila_valores = fila_sector.drop("Concepto")
    fila_valores = pd.to_numeric(fila_valores, errors="coerce")

    temp_clientes = pd.DataFrame({
        "sector": fila_valores.index,
        "coeficiente": fila_valores.values
    })
    temp_clientes = temp_clientes[temp_clientes["sector"].str.match(r"^\d")]
    top_clientes = temp_clientes.sort_values("coeficiente", ascending=False).head(top_n)

    # convertir a lista de diccionarios
    lista_clientes = []
    for _, row in top_clientes.iterrows():
        lista_clientes.append({
            "sector": row["sector"],
            "coeficiente": round(float(row["coeficiente"]), 6),
            "porcentaje": round(float(row["coeficiente"]) * 100, 2)
        })

    # obtener proveedores (columna)
    columna_valores = pd.to_numeric(df[nombre_columna], errors="coerce")
    temp_proveedores = pd.DataFrame({
        "sector": df["Concepto"].values,
        "coeficiente": columna_valores.values
    })
    temp_proveedores = temp_proveedores[temp_proveedores["sector"].str.match(r"^\d")]
    top_proveedores = temp_proveedores.sort_values("coeficiente", ascending=False).head(top_n)

    # convertir a lista de diccionarios
    lista_proveedores = []
    for _, row in top_proveedores.iterrows():
        lista_proveedores.append({
            "sector": row["sector"],
            "coeficiente": round(float(row["coeficiente"]), 6),
            "porcentaje": round(float(row["coeficiente"]) * 100, 2)
        })

    # devolver resultado
    return {
        "codigo": codigo_scian,
        "sector": nombre_fila,
        "top_clientes": lista_clientes,
        "top_proveedores": lista_proveedores
    }

# funcion auxiliar: mostrar_resultado
def mostrar_resultado(resultado):
    """imprime el resultado en la terminal"""
    if not resultado:
        return

    print(f"\n{'=' * 60}")
    print(f"sector: {resultado['sector']}")
    print(f"{'=' * 60}")

    print(f"\ntop {len(resultado['top_clientes'])} clientes:")
    for i, cliente in enumerate(resultado['top_clientes'], 1):
        print(f"   {i}. {cliente['sector']}")
        print(f"      → {cliente['porcentaje']}%")

    print(f"\ntop {len(resultado['top_proveedores'])} proveedores:")
    for i, proveedor in enumerate(resultado['top_proveedores'], 1):
        print(f"   {i}. {proveedor['sector']}")
        print(f"      → {proveedor['porcentaje']}%")


# ejecucion principal
if __name__ == "__main__":
    print("=" * 60)
    print("analisis de multiples sectores")
    print("=" * 60)

    # probar con 3 sectores diferentes
    sectores_a_probar = ["3111", "3113", "5241"]

    # guardar todos los resultados en una lista
    todos_los_resultados = []

    for codigo in sectores_a_probar:
        resultado = analizar_sector(codigo)
        mostrar_resultado(resultado)
        
        if resultado:
            todos_los_resultados.append(resultado)

    # guardar en archivo JSON
    ruta_salida = "resultados.json"
    
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(todos_los_resultados, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"analisis completado")
    print(f"resultados guardados en: {ruta_salida}")
    print(f"   total de sectores analizados: {len(todos_los_resultados)}")
    print(f"{'=' * 60}")
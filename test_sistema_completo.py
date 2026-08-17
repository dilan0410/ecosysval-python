"""
==========================================
SISTEMA COMPLETO v1
==========================================
Objetivo: Combinar MIP + Clasificación para dar
recomendaciones enriquecidas con categorías.
"""

import pandas as pd
import json

# ==========================================
# CONFIGURACIÓN
# ==========================================
RUTA_MIP = "data/MIP_2013.xlsx"
RUTA_CLASIFICACION = "data/clasificacion_2024.xlsx"
FILA_ENCABEZADOS = 4
TOP_N = 5

HOJAS_CATEGORIAS = [
    "Clave",
    "Articulador",
    "Multicadena impulsor",
    "Potenciales",
    "Multicadenas",
    "ARTICULADOS GRISES",
    "NO ARTICULADO",
]


# ==========================================
# FUNCIÓN: cargar_clasificacion()
# ==========================================
def cargar_clasificacion():
    """Carga las categorías de todos los sectores desde el Excel."""
    clasificacion = {}

    for nombre_hoja in HOJAS_CATEGORIAS:
        df = pd.read_excel(RUTA_CLASIFICACION, sheet_name=nombre_hoja)

        col_codigo = None
        for col in df.columns:
            if "CIIU" in str(col) or "SCIAN" in str(col):
                col_codigo = col
                break

        if not col_codigo:
            continue

        codigos = df[col_codigo].dropna()
        for codigo in codigos:
            codigo_limpio = str(codigo).strip()
            if codigo_limpio.endswith(".0"):
                codigo_limpio = codigo_limpio[:-2]
            clasificacion[codigo_limpio] = nombre_hoja

    return clasificacion


# ==========================================
# FUNCIÓN AUXILIAR: extraer_codigo_de_sector()
# ==========================================
def extraer_codigo_de_sector(texto_sector):
    """
    Extrae el código SCIAN de un texto como:
    '1122 - Explotación de porcinos' → '1122'
    """
    partes = texto_sector.strip().split(" - ")
    if len(partes) > 0:
        return partes[0].strip()
    return None


# ==========================================
# FUNCIÓN PRINCIPAL: analizar_sector()
# ==========================================
def analizar_sector(codigo_scian, clasificacion, top_n=5):
    """
    Analiza un sector y devuelve sus top clientes/proveedores
    CON su categoría económica.
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

    # ---------- 3. OBTENER CATEGORÍA DEL SECTOR PRINCIPAL ----------
    categoria_principal = clasificacion.get(codigo_scian, "Sin clasificar")

    # ---------- 4. OBTENER CLIENTES ----------
    fila_sector = df[df["Concepto"] == nombre_fila].iloc[0]
    fila_valores = fila_sector.drop("Concepto")
    fila_valores = pd.to_numeric(fila_valores, errors="coerce")

    temp_clientes = pd.DataFrame({
        "sector": fila_valores.index,
        "coeficiente": fila_valores.values
    })
    temp_clientes = temp_clientes[temp_clientes["sector"].str.match(r"^\d")]
    top_clientes = temp_clientes.sort_values("coeficiente", ascending=False).head(top_n)

    lista_clientes = []
    for _, row in top_clientes.iterrows():
        # NUEVO: Extraer código y obtener categoría
        codigo = extraer_codigo_de_sector(row["sector"])
        categoria = clasificacion.get(codigo, "Sin clasificar")

        lista_clientes.append({
            "codigo": codigo,
            "sector": row["sector"],
            "categoria": categoria,  # NUEVO
            "coeficiente": round(float(row["coeficiente"]), 6),
            "porcentaje": round(float(row["coeficiente"]) * 100, 2)
        })

    # ---------- 5. OBTENER PROVEEDORES ----------
    columna_valores = pd.to_numeric(df[nombre_columna], errors="coerce")
    temp_proveedores = pd.DataFrame({
        "sector": df["Concepto"].values,
        "coeficiente": columna_valores.values
    })
    temp_proveedores = temp_proveedores[temp_proveedores["sector"].str.match(r"^\d")]
    top_proveedores = temp_proveedores.sort_values("coeficiente", ascending=False).head(top_n)

    lista_proveedores = []
    for _, row in top_proveedores.iterrows():
        # NUEVO: Extraer código y obtener categoría
        codigo = extraer_codigo_de_sector(row["sector"])
        categoria = clasificacion.get(codigo, "Sin clasificar")

        lista_proveedores.append({
            "codigo": codigo,
            "sector": row["sector"],
            "categoria": categoria,  # NUEVO
            "coeficiente": round(float(row["coeficiente"]), 6),
            "porcentaje": round(float(row["coeficiente"]) * 100, 2)
        })

    # ---------- 6. DEVOLVER RESULTADO COMPLETO ----------
    return {
        "codigo": codigo_scian,
        "sector": nombre_fila,
        "categoria": categoria_principal,  # NUEVO
        "top_clientes": lista_clientes,
        "top_proveedores": lista_proveedores
    }


# ==========================================
# FUNCIÓN AUXILIAR: mostrar_resultado()
# ==========================================
def mostrar_resultado(resultado):
    """Imprime el resultado con categorías visibles."""
    if not resultado:
        return

    print(f"\n{' ' * 70}")
    print(f"sector: {resultado['sector']}")
    print(f"  categoria: {resultado['categoria']}")  # NUEVO
    print(f"{' ' * 70}")

    print(f"\ntop {len(resultado['top_clientes'])} clientes:")
    for i, cliente in enumerate(resultado['top_clientes'], 1):
        print(f"   {i}. [{cliente['categoria']:<22}] {cliente['sector']}")
        print(f"      → {cliente['porcentaje']}%")

    print(f"\ntop {len(resultado['top_proveedores'])} proveedores:")
    for i, proveedor in enumerate(resultado['top_proveedores'], 1):
        print(f"   {i}. [{proveedor['categoria']:<22}] {proveedor['sector']}")
        print(f"      → {proveedor['porcentaje']}%")


# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================
if __name__ == "__main__":
    
    print("sistema completo: MIP + CLASIFICACION")
    

    # Cargar clasificación UNA sola vez (más eficiente)
    print("\nCargando clasificacion de sectores...")
    clasificacion = cargar_clasificacion()
    print(f"{len(clasificacion)} sectores clasificados")

    # Probar con 3 sectores diferentes
    sectores_a_probar = ["3111", "3113", "5241"]
    todos_los_resultados = []

    for codigo in sectores_a_probar:
        resultado = analizar_sector(codigo, clasificacion)
        mostrar_resultado(resultado)

        if resultado:
            todos_los_resultados.append(resultado)

    # Guardar en JSON enriquecido
    ruta_salida = "resultados_completos.json"
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(todos_los_resultados, f, indent=2, ensure_ascii=False)

    print(f"\n{' ' * 70}")
    print(f"sistema completado")
    print(f"resultados guardados en: {ruta_salida}")
    print(f"   total de sectores analizados: {len(todos_los_resultados)}")
    print(f"{' ' * 70}")
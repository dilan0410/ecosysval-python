"""
==========================================
TEST CLASIFICACIÓN v2 - Función Reutilizable
==========================================
Objetivo: Crear una función que lea todas las
categorías y devuelva un diccionario de consulta.
"""

import pandas as pd

# ==========================================
# CONFIGURACIÓN
# ==========================================
RUTA_CLASIFICACION = "data/clasificacion_2024.xlsx"

# Solo las 7 hojas de categorías (ignoramos Sheet1)
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
    """
    Lee todas las hojas del Excel de clasificación y devuelve
    un diccionario donde:
        - clave: código SCIAN (string)
        - valor: categoría del sector (string)

    Returns:
        dict: {"3111": "Articulador", "5241": "Clave", ...}
    """
    clasificacion = {}

    for nombre_hoja in HOJAS_CATEGORIAS:
        # Leer la hoja
        df = pd.read_excel(RUTA_CLASIFICACION, sheet_name=nombre_hoja)

        # Detectar nombre de la columna código
        # (siempre es la primera columna que contiene "CIIU")
        col_codigo = None
        for col in df.columns:
            if "CIIU" in str(col) or "SCIAN" in str(col):
                col_codigo = col
                break

        if not col_codigo:
            print(f"No se encontró columna de código en '{nombre_hoja}'")
            continue

        # Extraer códigos (ignorando NaN)
        codigos = df[col_codigo].dropna()

        # Agregar al diccionario
        for codigo in codigos:
            # Convertir a string y limpiar espacios
            codigo_limpio = str(codigo).strip()

            # Si el código es tipo "1111.0" (float), quitar el .0
            if codigo_limpio.endswith(".0"):
                codigo_limpio = codigo_limpio[:-2]

            clasificacion[codigo_limpio] = nombre_hoja

    return clasificacion


# ==========================================
# FUNCIÓN AUXILIAR: obtener_categoria()
# ==========================================
def obtener_categoria(codigo_scian, clasificacion):
    """
    Devuelve la categoría de un sector.

    Args:
        codigo_scian (str): Código SCIAN
        clasificacion (dict): Diccionario de categorías

    Returns:
        str: Nombre de la categoría o "Sin clasificar" si no existe
    """
    return clasificacion.get(str(codigo_scian).strip(), "Sin clasificar")


# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================
if __name__ == "__main__":
    print("=" * 70)
    print("CARGANDO CLASIFICACIÓN DE SECTORES")
    print("=" * 70)

    # Cargar la clasificación
    clasificacion = cargar_clasificacion()

    print(f"\nTotal de sectores clasificados: {len(clasificacion)}")

    # ==========================================
    # ESTADÍSTICAS POR CATEGORÍA
    # ==========================================
    print(f"\nDistribución por categoría:")
    contador = {}
    for categoria in clasificacion.values():
        contador[categoria] = contador.get(categoria, 0) + 1

    for categoria, cantidad in sorted(contador.items(), key=lambda x: -x[1]):
        print(f"   • {categoria:.<30} {cantidad} sectores")

    # ==========================================
    # PRUEBA CON VARIOS SECTORES
    # ==========================================
    print(f"\n{'=' * 70}")
    print("PRUEBA: Consultar categoría de varios sectores")
    print(f"{'=' * 70}")

    sectores_prueba = [
        "3111",   # Alimentos animales
        "3113",   # Chocolates
        "5241",   # Seguros
        "1111",   # Cultivo semillas
        "1122",   # Porcinos
        "9999",   # No existe (prueba)
    ]

    for codigo in sectores_prueba:
        categoria = obtener_categoria(codigo, clasificacion)
        print(f"   {codigo} → {categoria}")

    print(f"\n{'=' * 70}")
    print("EJECUCIÓN COMPLETADA")
    print(f"{'=' * 70}")
"""
==========================================
CLASIFICACIÓN SERVICE
==========================================
Servicio para leer y consultar las categorías
de sectores desde el Excel de clasificación 2024.
"""

import pandas as pd
from app.core.config import RUTA_CLASIFICACION, HOJAS_CATEGORIAS


# ==========================================
# CACHE GLOBAL
# ==========================================
# Cargamos la clasificación UNA sola vez al iniciar
# En vez de leer el Excel cada vez que se llama la función
_clasificacion_cache = None


# ==========================================
# CARGAR CLASIFICACIÓN
# ==========================================
def cargar_clasificacion():
    """
    Lee todas las hojas del Excel de clasificación y devuelve
    un diccionario con la categoría de cada sector.

    Returns:
        dict: {"3111": "Articulador", "5241": "Clave", ...}
    """
    global _clasificacion_cache

    # Si ya está cargada, devolverla directamente (cache)
    if _clasificacion_cache is not None:
        return _clasificacion_cache

    clasificacion = {}

    for nombre_hoja in HOJAS_CATEGORIAS:
        df = pd.read_excel(RUTA_CLASIFICACION, sheet_name=nombre_hoja)

        # Detectar columna código
        col_codigo = None
        for col in df.columns:
            if "CIIU" in str(col) or "SCIAN" in str(col):
                col_codigo = col
                break

        if not col_codigo:
            continue

        # Extraer códigos
        codigos = df[col_codigo].dropna()
        for codigo in codigos:
            codigo_limpio = str(codigo).strip()
            if codigo_limpio.endswith(".0"):
                codigo_limpio = codigo_limpio[:-2]
            clasificacion[codigo_limpio] = nombre_hoja

    # Guardar en cache para próximas llamadas
    _clasificacion_cache = clasificacion

    return clasificacion


# ==========================================
# OBTENER CATEGORÍA DE UN SECTOR
# ==========================================
def obtener_categoria(codigo_scian):
    """
    Devuelve la categoría de un sector específico.

    Args:
        codigo_scian (str): Código SCIAN del sector

    Returns:
        str: Nombre de la categoría o "Sin clasificar"
    """
    clasificacion = cargar_clasificacion()
    return clasificacion.get(str(codigo_scian).strip(), "Sin clasificar")


# ==========================================
# OBTENER ESTADÍSTICAS DE CATEGORÍAS
# ==========================================
def obtener_estadisticas():
    """
    Devuelve estadísticas de la clasificación:
    total y cantidad por categoría.

    Returns:
        dict: {"total": 319, "por_categoria": {"Clave": 31, ...}}
    """
    clasificacion = cargar_clasificacion()

    contador = {}
    for categoria in clasificacion.values():
        contador[categoria] = contador.get(categoria, 0) + 1

    # Ordenar de mayor a menor
    contador_ordenado = dict(
        sorted(contador.items(), key=lambda x: -x[1])
    )

    return {
        "total": len(clasificacion),
        "por_categoria": contador_ordenado
    }
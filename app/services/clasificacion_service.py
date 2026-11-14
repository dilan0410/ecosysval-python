"""

clasificacion service (actualizado con cascada)

"""

import pandas as pd
from app.core.config import RUTA_CLASIFICACION, HOJAS_CATEGORIAS

_clasificacion_cache = None

def cargar_clasificacion():
    global _clasificacion_cache
    if _clasificacion_cache is not None:
        return _clasificacion_cache

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

    _clasificacion_cache = clasificacion
    return clasificacion

def obtener_categoria(codigo_scian):
    """
    Busca la categoria. Si no encuentra 311811, busca 31181, luego 3118.
    """
    clasificacion = cargar_clasificacion()
    codigo = str(codigo_scian).strip()

    while len(codigo) >= 3:
        if codigo in clasificacion:
            return clasificacion[codigo]
        codigo = codigo[:-1]

    return "Sin clasificar"

def obtener_estadisticas():
    clasificacion = cargar_clasificacion()
    contador = {}
    for categoria in clasificacion.values():
        contador[categoria] = contador.get(categoria, 0) + 1

    contador_ordenado = dict(sorted(contador.items(), key=lambda x: -x[1]))
    return {
        "total": len(clasificacion),
        "por_categoria": contador_ordenado
    }
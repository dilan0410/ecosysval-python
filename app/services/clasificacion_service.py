"""
==========================================
SERVICIO DE CLASIFICACIÓN ESTRATÉGICA
==========================================
Carga las categorías estratégicas (Clave, Articulador, etc.) desde
data/clasificacion_2024.xlsx y resuelve la categoría de un sector.

Reglas de carga (explícitas, no silenciosas):
- Solo se aceptan claves que sean códigos SCIAN de 4 o 6 dígitos.
  Notas, encabezados repetidos o textos dentro de las hojas se
  rechazan y se registran como advertencia en el log.
- Si un código aparece en varias hojas, prevalece la ÚLTIMA hoja
  según el orden de HOJAS_CATEGORIAS (comportamiento histórico del
  sistema) y el conflicto se registra en el log. Los conflictos
  detectados pueden consultarse con obtener_conflictos().
- La normalización del código consultado se delega en
  codigo_service.normalizar_codigo (única vía autorizada).
"""

import logging
import re

import pandas as pd

from app.core.config import RUTA_CLASIFICACION, HOJAS_CATEGORIAS
from app.services.codigo_service import normalizar_codigo

logger = logging.getLogger(__name__)

_RE_CODIGO_VALIDO = re.compile(r"^(\d{4}|\d{6})$")

_clasificacion_cache = None
_conflictos_cache = []


def cargar_clasificacion():
    global _clasificacion_cache, _conflictos_cache
    if _clasificacion_cache is not None:
        return _clasificacion_cache

    clasificacion = {}
    conflictos = []
    for nombre_hoja in HOJAS_CATEGORIAS:
        df = pd.read_excel(RUTA_CLASIFICACION, sheet_name=nombre_hoja)

        col_codigo = None
        for col in df.columns:
            if "CIIU" in str(col) or "SCIAN" in str(col):
                col_codigo = col
                break

        if not col_codigo:
            logger.warning(
                "Hoja '%s' sin columna de código CIIU/SCIAN; se omite.", nombre_hoja
            )
            continue

        for codigo in df[col_codigo].dropna():
            codigo_limpio = str(codigo).strip()
            if codigo_limpio.endswith(".0"):
                codigo_limpio = codigo_limpio[:-2]

            if not _RE_CODIGO_VALIDO.match(codigo_limpio):
                logger.warning(
                    "Valor rechazado en hoja '%s': %r no es un código SCIAN.",
                    nombre_hoja, codigo_limpio,
                )
                continue

            if codigo_limpio in clasificacion and clasificacion[codigo_limpio] != nombre_hoja:
                conflictos.append({
                    "codigo": codigo_limpio,
                    "categoria_anterior": clasificacion[codigo_limpio],
                    "categoria_aplicada": nombre_hoja,
                })
                logger.warning(
                    "Conflicto de clasificación para %s: '%s' sobrescribe a '%s' "
                    "(prevalece la última hoja de HOJAS_CATEGORIAS).",
                    codigo_limpio, nombre_hoja, clasificacion[codigo_limpio],
                )

            clasificacion[codigo_limpio] = nombre_hoja

    _clasificacion_cache = clasificacion
    _conflictos_cache = conflictos
    return clasificacion


def obtener_conflictos():
    """Conflictos entre hojas detectados al cargar (última hoja gana)."""
    cargar_clasificacion()
    return list(_conflictos_cache)


def obtener_categoria(codigo_scian):
    """
    Devuelve la categoría estratégica de un código SCIAN.

    Si el código es de 6 dígitos y no tiene categoría propia, hereda
    la de su rama padre de 4 dígitos. Si ningún ancestro está
    clasificado, devuelve "Sin clasificar".

    Raises:
        CodigoInvalidoError: si el formato del código es inválido.
    """
    clasificacion = cargar_clasificacion()
    codigo = normalizar_codigo(codigo_scian)

    while len(codigo) >= 4:
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

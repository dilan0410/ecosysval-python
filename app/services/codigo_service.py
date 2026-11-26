"""
==========================================
SERVICIO CENTRAL DE CÓDIGOS SCIAN
==========================================
Única vía autorizada para normalizar códigos sectoriales y
homologarlos a ramas de la MIP 2013.

Toda resolución de códigos en la API (endpoints, servicios de
recomendaciones y de empresas) debe pasar por aquí. Ningún otro
módulo debe truncar, limpiar ni buscar códigos por su cuenta.

Reglas de resolución (en orden):
1. Exacta: el código de 4 dígitos existe como rama en la MIP.
2. Crosswalk: equivalencia explícita en data/crosswalk_scian_mip.csv.
3. Padre jerárquico: un código de 6 dígitos se agrega a su rama
   padre de 4 dígitos si ésta existe en la MIP (o tiene crosswalk).

Si ninguna regla aplica, se devuelve None y la capa API responde
404 con causa "sin_equivalencia_mip". Nunca se inventan relaciones.
"""

import csv
import logging
import re
from dataclasses import dataclass
from typing import Optional

from app.core.config import RUTA_CROSSWALK

logger = logging.getLogger(__name__)

_RE_CODIGO = re.compile(r"^\d+$")
LONGITUDES_VALIDAS = (4, 6)


class CodigoInvalidoError(ValueError):
    """El código no cumple el formato SCIAN aceptado (4 o 6 dígitos)."""


@dataclass(frozen=True)
class ResolucionSector:
    """Resultado trazable de homologar un código SCIAN a una rama MIP."""

    codigo_buscado: str          # Código ya normalizado que pidió el cliente
    codigo_resuelto: str         # Rama de 4 dígitos existente en la MIP
    metodo_mapeo: str            # exacto | padre_jerarquico | <metodo del crosswalk>
    nivel_agregacion: str        # ninguno | clase_a_rama | rama_equivalente


def normalizar_codigo(codigo) -> str:
    """
    Normaliza un código SCIAN a su forma canónica de string.

    Acepta enteros y strings; tolera espacios extremos y el sufijo
    ".0" que producen las lecturas numéricas de Excel.

    Raises:
        CodigoInvalidoError: si no son solo dígitos, si la longitud
            no es 4 o 6, o si trae ceros a la izquierda.
    """
    texto = str(codigo).strip()

    if texto.endswith(".0") and _RE_CODIGO.match(texto[:-2]):
        texto = texto[:-2]

    if not _RE_CODIGO.match(texto):
        raise CodigoInvalidoError(
            f"El código '{codigo}' no es un código SCIAN válido: "
            "debe contener solo dígitos."
        )
    if len(texto) not in LONGITUDES_VALIDAS:
        raise CodigoInvalidoError(
            f"El código '{codigo}' tiene {len(texto)} dígitos; "
            "se aceptan códigos SCIAN de 4 (rama) o 6 (clase) dígitos."
        )
    if texto.startswith("0"):
        raise CodigoInvalidoError(
            f"El código '{codigo}' no es un código SCIAN válido: "
            "no debe tener ceros a la izquierda."
        )
    return texto


_crosswalk_cache = None


def cargar_crosswalk() -> dict:
    """
    Carga la tabla puente codigo_origen -> fila de equivalencia.

    La tabla vive en data/crosswalk_scian_mip.csv y es la única
    fuente de equivalencias no jerárquicas. El archivo original
    data/MIP_2013.xlsx nunca se modifica.
    """
    global _crosswalk_cache
    if _crosswalk_cache is not None:
        return _crosswalk_cache

    crosswalk = {}
    with open(RUTA_CROSSWALK, newline="", encoding="utf-8-sig") as archivo:
        for fila in csv.DictReader(archivo):
            origen = normalizar_codigo(fila["codigo_origen"])
            destino = normalizar_codigo(fila["codigo_mip"])
            if len(destino) != 4:
                raise ValueError(
                    f"Crosswalk inválido: el destino {destino} no es una rama de 4 dígitos."
                )
            if origen in crosswalk:
                raise ValueError(
                    f"Crosswalk inválido: el código {origen} está duplicado."
                )
            crosswalk[origen] = {
                "codigo_mip": destino,
                "metodo_mapeo": (fila.get("metodo_mapeo") or "crosswalk").strip(),
                "nivel_agregacion": (fila.get("nivel_agregacion") or "clase_a_rama").strip(),
                "confianza": (fila.get("confianza") or "").strip(),
                "justificacion": (fila.get("justificacion") or "").strip(),
            }

    logger.info("Crosswalk SCIAN->MIP cargado: %d equivalencias.", len(crosswalk))
    _crosswalk_cache = crosswalk
    return crosswalk


def resolver_codigo_mip(codigo, codigos_mip) -> Optional[ResolucionSector]:
    """
    Homologa un código SCIAN a una rama existente de la MIP.

    Args:
        codigo: código tal como lo envió el cliente (se normaliza aquí).
        codigos_mip: conjunto de códigos de 4 dígitos presentes en la MIP.

    Returns:
        ResolucionSector si hay equivalencia, None si no existe ninguna
        (la capa API debe responder 404 con causa estructurada).

    Raises:
        CodigoInvalidoError: si el formato del código es inválido
            (la capa API debe responder 422).
    """
    buscado = normalizar_codigo(codigo)
    crosswalk = cargar_crosswalk()

    # 1) Coincidencia exacta con una rama MIP
    if len(buscado) == 4 and buscado in codigos_mip:
        return ResolucionSector(buscado, buscado, "exacto", "ninguno")

    # 2) Equivalencia explícita en la tabla puente
    equivalencia = crosswalk.get(buscado)
    if equivalencia and equivalencia["codigo_mip"] in codigos_mip:
        return ResolucionSector(
            codigo_buscado=buscado,
            codigo_resuelto=equivalencia["codigo_mip"],
            metodo_mapeo=equivalencia["metodo_mapeo"],
            nivel_agregacion=equivalencia["nivel_agregacion"],
        )

    # 3) Agregación jerárquica: clase de 6 dígitos -> rama padre de 4
    if len(buscado) == 6:
        padre = buscado[:4]
        if padre in codigos_mip:
            return ResolucionSector(buscado, padre, "padre_jerarquico", "clase_a_rama")
        equivalencia_padre = crosswalk.get(padre)
        if equivalencia_padre and equivalencia_padre["codigo_mip"] in codigos_mip:
            return ResolucionSector(
                codigo_buscado=buscado,
                codigo_resuelto=equivalencia_padre["codigo_mip"],
                metodo_mapeo="padre_crosswalk",
                nivel_agregacion="clase_a_rama",
            )

    return None

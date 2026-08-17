"""
==========================================
MODELOS PYDANTIC
==========================================
Modelos de datos que definen la ESTRUCTURA y VALIDACIÓN
de las respuestas de la API.

Equivalente a los DTOs de NestJS.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ==========================================
# MODELO: Sector Recomendado
# ==========================================
class SectorRecomendado(BaseModel):
    """
    Un sector recomendado (cliente o proveedor).

    Ejemplo:
    {
        "codigo": "1123",
        "sector": "1123 - Explotación avícola",
        "categoria": "Multicadena impulsor",
        "coeficiente": 0.322607,
        "porcentaje": 32.26
    }
    """
    codigo: str = Field(..., description="Código SCIAN del sector")
    sector: str = Field(..., description="Nombre completo del sector")
    categoria: str = Field(..., description="Categoría estratégica")
    coeficiente: float = Field(..., description="Coeficiente técnico (0-1)")
    porcentaje: float = Field(..., description="Porcentaje de relación")


# ==========================================
# MODELO: Recomendación Completa
# ==========================================
class RecomendacionCompleta(BaseModel):
    """
    Respuesta completa del análisis de un sector.

    Incluye:
    - Información del sector consultado
    - Top clientes con sus categorías
    - Top proveedores con sus categorías
    """
    codigo: str = Field(..., description="Código SCIAN consultado")
    sector: str = Field(..., description="Nombre del sector")
    categoria: str = Field(..., description="Categoría del sector consultado")
    top_clientes: List[SectorRecomendado] = Field(
        default=[],
        description="Sectores que le COMPRAN al sector consultado"
    )
    top_proveedores: List[SectorRecomendado] = Field(
        default=[],
        description="Sectores que le VENDEN al sector consultado"
    )


# ==========================================
# MODELO: Sector Simple (para listar)
# ==========================================
class SectorSimple(BaseModel):
    """
    Información básica de un sector (para listados).

    Ejemplo:
    {
        "codigo": "1111",
        "nombre": "1111 - Cultivo de semillas oleaginosas..."
    }
    """
    codigo: str = Field(..., description="Código SCIAN")
    nombre: str = Field(..., description="Nombre completo con código")


# ==========================================
# MODELO: Estadísticas
# ==========================================
class EstadisticasClasificacion(BaseModel):
    """
    Estadísticas de la clasificación de sectores.

    Ejemplo:
    {
        "total": 319,
        "por_categoria": {
            "Clave": 31,
            "Articulador": 8,
            ...
        }
    }
    """
    total: int = Field(..., description="Total de sectores clasificados")
    por_categoria: dict = Field(..., description="Cantidad por categoría")


# ==========================================
# MODELO: Respuesta de Error
# ==========================================
class ErrorResponse(BaseModel):
    """
    Estructura estándar para errores.
    """
    detail: str = Field(..., description="Descripción del error")
    codigo_solicitado: Optional[str] = Field(None, description="Código que causó el error")
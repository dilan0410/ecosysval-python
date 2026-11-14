"""
==========================================
MODELOS PYDANTIC: Recomendaciones
==========================================
Definición de esquemas de respuesta para FastAPI.
"""

from pydantic import BaseModel
from typing import List, Optional


class NodoRecomendacion(BaseModel):
    codigo: str
    sector: str
    categoria: str
    coeficiente: float
    porcentaje: float


class SectorSimple(BaseModel):
    codigo: str
    nombre: str


class EstadisticasClasificacion(BaseModel):
    total: int
    por_categoria: dict


class RecomendacionCompleta(BaseModel):
    codigo: str                                # Mantiene compatibilidad con Frontend
    codigo_buscado: Optional[str] = None       # El SCIAN ingresado (ej: 311811)
    codigo_resuelto: Optional[str] = None      # El SCIAN usado en MIP (ej: 3118)
    sector: str
    categoria: str
    top_clientes: List[NodoRecomendacion]
    top_proveedores: List[NodoRecomendacion]
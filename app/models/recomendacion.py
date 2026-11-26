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
    coeficiente: float          # Coeficiente técnico MIP (nunca <= 0 en la respuesta)
    porcentaje: float           # Participación relativa normalizada (%) sobre coeficientes positivos
    participacion_relativa: float = 0.0  # Mismo valor que "porcentaje", nombre semántico explícito


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
    codigo_mip: Optional[str] = None           # Rama MIP homologada (alias de codigo_resuelto)
    metodo_mapeo: Optional[str] = None         # exacto | padre_jerarquico | método del crosswalk
    nivel_agregacion: Optional[str] = None     # ninguno | clase_a_rama | rama_equivalente
    sector: str
    categoria: str
    top_clientes: List[NodoRecomendacion]
    top_proveedores: List[NodoRecomendacion]
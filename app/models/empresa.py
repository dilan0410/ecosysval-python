"""
==========================================
MODELOS PYDANTIC: Empresas y socios B2B
==========================================
Esquemas de respuesta para el directorio empresarial (hoja Sheet1
de data/clasificacion_2024.xlsx) y el emparejamiento de socios.

Nota de datos: la fuente no incluye razón social; cada registro se
identifica con "registro_id" (número de fila en la hoja de origen)
y se exponen los datos de contacto disponibles en la fuente.
"""

from pydantic import BaseModel
from typing import List, Optional


class Empresa(BaseModel):
    registro_id: int                      # Fila de origen en Sheet1 (encabezado = fila 1)
    codigo_scian: str                     # Código de 4 dígitos registrado en la fuente
    codigo_mip: Optional[str] = None      # Rama MIP homologada (None si no tiene equivalencia)
    entidad: str
    per_ocu: Optional[str] = None         # Rango de personal ocupado
    descripcion_actividad: Optional[str] = None
    telefono: Optional[str] = None
    correoelec: Optional[str] = None
    www: Optional[str] = None


class ListaEmpresas(BaseModel):
    total: int
    limite: int
    desplazamiento: int
    empresas: List[Empresa]


class SectorSocios(BaseModel):
    codigo: str                           # Rama MIP del sector relacionado
    sector: str
    categoria: str
    coeficiente: float                    # Coeficiente técnico (> 0 siempre)
    participacion_relativa: float         # Peso normalizado del coeficiente (%)
    total_empresas: int                   # Empresas disponibles en ese sector
    empresas: List[Empresa]               # Muestra limitada por "por_sector"


class RespuestaSocios(BaseModel):
    codigo_buscado: str
    codigo_resuelto: str                  # Rama MIP de la empresa/sector origen
    metodo_mapeo: Optional[str] = None
    nivel_agregacion: Optional[str] = None
    sector: str                           # Sector MIP origen
    categoria: str
    socios_clientes: List[SectorSocios]       # Sectores que le compran -> empresas candidatas
    socios_proveedores: List[SectorSocios]    # Sectores que le venden -> empresas candidatas

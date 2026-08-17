"""
==========================================
ENDPOINTS: Recomendaciones
==========================================
Endpoints REST para el Sistema Inteligente Económico.

Endpoints disponibles:
- GET /recomendaciones/sectores           → Lista todos los sectores
- GET /recomendaciones/estadisticas       → Estadísticas de clasificación
- GET /recomendaciones/sector/{codigo}    → Info de un sector
- GET /recomendaciones/{codigo}           → Recomendaciones completas
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List

from app.services.mip_service import analizar_sector, listar_sectores
from app.services.clasificacion_service import obtener_estadisticas, obtener_categoria
from app.models.recomendacion import (
    RecomendacionCompleta,
    SectorSimple,
    EstadisticasClasificacion,
)
from app.core.config import TOP_N_DEFAULT, TOP_N_MAX


# ==========================================
# CREAR ROUTER
# ==========================================
router = APIRouter(
    prefix="/recomendaciones",
    tags=["Recomendaciones"],  # Categoría en Swagger
)


# ==========================================
# GET /recomendaciones/sectores
# ==========================================
@router.get(
    "/sectores",
    response_model=List[SectorSimple],
    summary="Listar todos los sectores",
    description="Devuelve todos los sectores SCIAN disponibles en la MIP."
)
def obtener_sectores():
    """Lista los 262 sectores económicos disponibles."""
    return listar_sectores()


# ==========================================
# GET /recomendaciones/estadisticas
# ==========================================
@router.get(
    "/estadisticas",
    response_model=EstadisticasClasificacion,
    summary="Estadísticas de clasificación",
    description="Devuelve el total de sectores clasificados y cuántos hay por cada categoría."
)
def obtener_estadisticas_endpoint():
    """Estadísticas globales del sistema de clasificación."""
    return obtener_estadisticas()


# ==========================================
# GET /recomendaciones/sector/{codigo}
# ==========================================
@router.get(
    "/sector/{codigo}",
    summary="Información básica de un sector",
    description="Devuelve el código, nombre y categoría de un sector específico."
)
def obtener_info_sector(codigo: str):
    """
    Info básica de un sector.

    Args:
        codigo: Código SCIAN (ej: "3111")
    """
    categoria = obtener_categoria(codigo)

    # Verificar que el sector exista en la MIP
    sectores = listar_sectores()
    sector_info = next(
        (s for s in sectores if s["codigo"] == codigo),
        None
    )

    if not sector_info:
        raise HTTPException(
            status_code=404,
            detail=f"Sector '{codigo}' no encontrado en la MIP"
        )

    return {
        "codigo": codigo,
        "nombre": sector_info["nombre"],
        "categoria": categoria
    }


# ==========================================
# GET /recomendaciones/{codigo}
# ==========================================
@router.get(
    "/{codigo}",
    response_model=RecomendacionCompleta,
    summary="Recomendaciones completas de un sector",
    description=(
        "Devuelve el análisis completo del sector: sus top clientes y proveedores "
        "con las categorías estratégicas correspondientes. "
        "Fuente: MIP 2013 (INEGI) + Clasificación 2024."
    ),
    responses={
        200: {"description": "Recomendaciones generadas exitosamente"},
        404: {"description": "Sector no encontrado"},
    }
)
def obtener_recomendaciones(
    codigo: str,
    top_n: int = Query(
        default=TOP_N_DEFAULT,
        ge=1,
        le=TOP_N_MAX,
        description=f"Cantidad de resultados (1-{TOP_N_MAX})"
    )
):
    """
    Genera recomendaciones para un sector.

    Args:
        codigo: Código SCIAN del sector (ej: "3111")
        top_n: Cantidad de clientes/proveedores a devolver
    """
    resultado = analizar_sector(codigo, top_n=top_n)

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail=f"Sector '{codigo}' no encontrado en la MIP. "
                   f"Prueba con /recomendaciones/sectores para ver los disponibles."
        )

    return resultado
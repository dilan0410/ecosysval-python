"""
==========================================
ENDPOINTS: Empresas y socios B2B
==========================================
Endpoints REST sobre el directorio empresarial (Sheet1 de
data/clasificacion_2024.xlsx) y el emparejamiento de socios.

- GET /empresas                  -> Directorio empresarial paginado
- GET /empresas/socios/{codigo}  -> Socios B2B por sector

Manejo de errores (convención del proyecto):
- 422 formato_invalido: el código no es SCIAN de 4 o 6 dígitos.
- 404 sin_equivalencia_mip: el código es válido pero no tiene
  equivalencia en la MIP 2013 ni en la tabla puente (crosswalk).
"""

from fastapi import APIRouter, HTTPException, Query

from app.models.empresa import ListaEmpresas, RespuestaSocios
from app.services.codigo_service import CodigoInvalidoError
from app.services.empresas_service import listar_empresas, buscar_socios
from app.core.config import TOP_N_DEFAULT, TOP_N_MAX


router = APIRouter(
    prefix="/empresas",
    tags=["Empresas"],
)


def _error_formato(codigo: str, exc: CodigoInvalidoError) -> HTTPException:
    return HTTPException(
        status_code=422,
        detail={
            "causa": "formato_invalido",
            "codigo": codigo,
            "mensaje": str(exc),
        },
    )


def _error_sin_equivalencia(codigo: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={
            "causa": "sin_equivalencia_mip",
            "codigo": codigo,
            "mensaje": (
                f"El código '{codigo}' es válido pero no tiene equivalencia "
                "en la MIP 2013 ni en la tabla puente (crosswalk_scian_mip.csv). "
                "Consulta /recomendaciones/sectores para ver las ramas disponibles."
            ),
        },
    )


@router.get(
    "",
    response_model=ListaEmpresas,
    summary="Directorio empresarial",
    description=(
        "Lista las empresas del directorio (Sheet1) con paginación. "
        "Cada empresa incluye su código SCIAN y su rama MIP homologada "
        "(null cuando el código aún no tiene equivalencia)."
    ),
)
def obtener_empresas(
    codigo_scian: str = Query(default=None, description="Filtrar por código SCIAN de 4 dígitos"),
    entidad: str = Query(default=None, description="Filtrar por entidad federativa (texto exacto)"),
    limite: int = Query(default=50, ge=1, le=200),
    desplazamiento: int = Query(default=0, ge=0),
):
    try:
        total, empresas = listar_empresas(
            codigo_scian=codigo_scian,
            entidad=entidad,
            limite=limite,
            desplazamiento=desplazamiento,
        )
    except CodigoInvalidoError as exc:
        raise _error_formato(codigo_scian, exc)
    return {
        "total": total,
        "limite": limite,
        "desplazamiento": desplazamiento,
        "empresas": empresas,
    }


@router.get(
    "/socios/{codigo}",
    response_model=RespuestaSocios,
    summary="Socios B2B de un sector",
    description=(
        "Empareja socios para las empresas de un sector: homologa el código "
        "a su rama MIP, calcula los sectores clientes y proveedores con "
        "coeficiente técnico > 0 y devuelve las empresas reales de esos "
        "sectores registradas en el directorio."
    ),
    responses={
        200: {"description": "Socios generados exitosamente"},
        404: {"description": "Código sin equivalencia en la MIP"},
        422: {"description": "Formato de código inválido"},
    },
)
def obtener_socios(
    codigo: str,
    top_n: int = Query(
        default=TOP_N_DEFAULT, ge=1, le=TOP_N_MAX,
        description=f"Sectores relacionados por grupo (1-{TOP_N_MAX})",
    ),
    por_sector: int = Query(
        default=5, ge=1, le=20,
        description="Empresas a mostrar por cada sector relacionado (1-20)",
    ),
    entidad: str = Query(
        default=None,
        description="Limitar los socios a una entidad federativa (texto exacto)",
    ),
):
    try:
        resultado = buscar_socios(
            codigo, top_n=top_n, por_sector=por_sector, entidad=entidad
        )
    except CodigoInvalidoError as exc:
        raise _error_formato(codigo, exc)

    if resultado is None:
        raise _error_sin_equivalencia(codigo)

    return resultado

"""
==========================================
SERVICIO DE EMPRESAS Y SOCIOS B2B
==========================================
Carga el directorio empresarial de la hoja Sheet1 de
data/clasificacion_2024.xlsx y construye el emparejamiento
empresa -> sector MIP -> sectores relacionados -> empresas socias.

La homologación de códigos se delega en la vía central
(mip_service.resolver_sector); las empresas cuyo código no tiene
equivalencia MIP quedan visibles en el directorio con
codigo_mip = None, pero nunca generan socios ficticios.
"""

import logging
from typing import Optional

import pandas as pd

from app.core.config import RUTA_CLASIFICACION, HOJA_EMPRESAS, TOP_N_DEFAULT
from app.services.codigo_service import CodigoInvalidoError, normalizar_codigo
from app.services.mip_service import analizar_sector, resolver_sector

logger = logging.getLogger(__name__)

_empresas_cache = None
_indice_mip_cache = None


def _limpiar_contacto(valor):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    if texto.endswith(".0") and texto[:-2].isdigit():
        texto = texto[:-2]
    if texto.lower() in ("", "sin dato", "nan", "none"):
        return None
    return texto


def _limpiar_texto(valor):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    return texto or None


def cargar_empresas():
    """Carga el directorio empresarial completo (con caché en memoria)."""
    global _empresas_cache
    if _empresas_cache is not None:
        return _empresas_cache

    df = pd.read_excel(RUTA_CLASIFICACION, sheet_name=HOJA_EMPRESAS)

    empresas = []
    for indice, fila in df.iterrows():
        codigo_crudo = fila["Código CIIU"]
        if pd.isna(codigo_crudo):
            continue
        codigo = str(codigo_crudo).strip()
        if codigo.endswith(".0"):
            codigo = codigo[:-2]

        empresas.append({
            "registro_id": int(indice) + 2,  # +1 encabezado, +1 base 1
            "codigo_scian": codigo,
            "codigo_mip": None,  # Se completa en el índice por rama MIP
            "entidad": _limpiar_texto(fila["entidad"]) or "",
            "per_ocu": _limpiar_texto(fila["per_ocu"]),
            "descripcion_actividad": _limpiar_texto(fila["Descripción de la Actividad"]),
            "telefono": _limpiar_contacto(fila["telefono"]),
            "correoelec": _limpiar_contacto(fila["correoelec"]),
            "www": _limpiar_contacto(fila["www"]),
        })

    logger.info("Directorio empresarial cargado: %d registros.", len(empresas))
    _empresas_cache = empresas
    return empresas


def _indice_por_rama_mip():
    """
    Agrupa las empresas por su rama MIP homologada.

    La homologación se calcula una sola vez por código distinto
    usando la resolución centralizada.
    """
    global _indice_mip_cache
    if _indice_mip_cache is not None:
        return _indice_mip_cache

    empresas = cargar_empresas()
    homologacion = {}
    for empresa in empresas:
        codigo = empresa["codigo_scian"]
        if codigo not in homologacion:
            try:
                resolucion = resolver_sector(codigo)
                homologacion[codigo] = resolucion.codigo_resuelto if resolucion else None
            except CodigoInvalidoError:
                homologacion[codigo] = None
        empresa["codigo_mip"] = homologacion[codigo]

    indice = {}
    for empresa in empresas:
        if empresa["codigo_mip"]:
            indice.setdefault(empresa["codigo_mip"], []).append(empresa)

    sin_equivalencia = sum(1 for e in empresas if not e["codigo_mip"])
    logger.info(
        "Empresas por rama MIP: %d con equivalencia, %d sin equivalencia.",
        len(empresas) - sin_equivalencia, sin_equivalencia,
    )
    _indice_mip_cache = indice
    return indice


def listar_empresas(codigo_scian=None, entidad=None, limite=50, desplazamiento=0):
    """
    Lista empresas del directorio con filtros opcionales.

    Returns:
        (total, empresas) donde total es el conteo tras los filtros.

    Raises:
        CodigoInvalidoError: si el filtro de código tiene formato inválido.
    """
    empresas = cargar_empresas()
    _indice_por_rama_mip()  # Completa el campo codigo_mip de cada empresa

    filtradas = empresas
    if codigo_scian is not None:
        codigo = normalizar_codigo(codigo_scian)
        filtradas = [e for e in filtradas if e["codigo_scian"] == codigo]
    if entidad:
        buscada = entidad.strip().lower()
        filtradas = [e for e in filtradas if e["entidad"].lower() == buscada]

    total = len(filtradas)
    return total, filtradas[desplazamiento:desplazamiento + limite]


def _empresas_del_sector(indice, codigo_mip, entidad, por_sector):
    empresas = indice.get(codigo_mip, [])
    if entidad:
        buscada = entidad.strip().lower()
        empresas = [e for e in empresas if e["entidad"].lower() == buscada]
    return len(empresas), empresas[:por_sector]


def buscar_socios(codigo_scian, top_n=TOP_N_DEFAULT, por_sector=5, entidad=None):
    """
    Empareja socios B2B para las empresas de un sector.

    Flujo: código -> homologación MIP centralizada -> análisis MIP
    (solo coeficientes > 0) -> empresas reales de cada sector
    relacionado, del directorio Sheet1.

    Returns:
        dict compatible con RespuestaSocios, o None si el código no
        tiene equivalencia MIP (la API responde 404 estructurado).

    Raises:
        CodigoInvalidoError: formato inválido (la API responde 422).
    """
    analisis = analizar_sector(codigo_scian, top_n=top_n)
    if analisis is None:
        return None

    indice = _indice_por_rama_mip()

    def construir(nodos):
        sectores = []
        for nodo in nodos:
            total, muestra = _empresas_del_sector(
                indice, nodo["codigo"], entidad, por_sector
            )
            sectores.append({
                "codigo": nodo["codigo"],
                "sector": nodo["sector"],
                "categoria": nodo["categoria"],
                "coeficiente": nodo["coeficiente"],
                "participacion_relativa": nodo["participacion_relativa"],
                "total_empresas": total,
                "empresas": muestra,
            })
        return sectores

    return {
        "codigo_buscado": analisis["codigo_buscado"],
        "codigo_resuelto": analisis["codigo_resuelto"],
        "metodo_mapeo": analisis["metodo_mapeo"],
        "nivel_agregacion": analisis["nivel_agregacion"],
        "sector": analisis["sector"],
        "categoria": analisis["categoria"],
        "socios_clientes": construir(analisis["top_clientes"]),
        "socios_proveedores": construir(analisis["top_proveedores"]),
    }

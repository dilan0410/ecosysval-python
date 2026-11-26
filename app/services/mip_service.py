"""
==========================================
SERVICIO DE MATRIZ INSUMO-PRODUCTO (MIP)
==========================================
Analiza la Matriz Insumo-Producto 2013 (INEGI) y genera las
relaciones sectoriales de clientes y proveedores.

Reglas analíticas obligatorias:
- La homologación código SCIAN -> rama MIP se delega SIEMPRE en
  codigo_service.resolver_codigo_mip (resolución centralizada).
- Filtrado estricto: jamás se emiten relaciones con coeficiente
  técnico <= 0. Si un sector no tiene clientes/proveedores con
  coeficiente positivo, la lista se devuelve vacía; no se rellena.
- El campo "porcentaje" es la participación relativa normalizada
  del coeficiente dentro del total de coeficientes positivos del
  flujo (fila o columna), NO el coeficiente técnico bruto x 100.
- El archivo data/MIP_2013.xlsx es de solo lectura: nunca se
  modifica; las equivalencias viven en el crosswalk.
"""

import pandas as pd

from app.core.config import RUTA_MIP, FILA_ENCABEZADOS_MIP, TOP_N_DEFAULT
from app.services.clasificacion_service import obtener_categoria
from app.services.codigo_service import resolver_codigo_mip

_mip_cache = None


def cargar_mip():
    global _mip_cache
    if _mip_cache is not None:
        return _mip_cache

    df = pd.read_excel(RUTA_MIP, header=FILA_ENCABEZADOS_MIP)
    df = df[df["Concepto"].notna()]
    df = df[~df["Concepto"].str.startswith("Fuente:", na=False)]
    df["Concepto"] = df["Concepto"].str.strip()
    df.columns = [str(col).strip() for col in df.columns]

    _mip_cache = df
    return df


def _extraer_codigo(texto_sector):
    partes = texto_sector.strip().split(" - ")
    return partes[0].strip() if partes else None


def _codigos_mip(df):
    """Conjunto de códigos de rama (4 dígitos) existentes en la MIP."""
    codigos = set()
    for concepto in df["Concepto"]:
        codigo = _extraer_codigo(str(concepto))
        if codigo and codigo.isdigit() and len(codigo) == 4:
            codigos.add(codigo)
    return codigos


def resolver_sector(codigo_scian):
    """
    Homologa un código SCIAN a una rama MIP usando la vía central.

    Returns:
        ResolucionSector o None si no hay equivalencia (la capa API
        responde 404 con causa "sin_equivalencia_mip").

    Raises:
        CodigoInvalidoError: formato inválido (la capa API responde 422).
    """
    df = cargar_mip()
    return resolver_codigo_mip(codigo_scian, _codigos_mip(df))


def _nombre_sector(df, codigo_resuelto):
    for concepto in df["Concepto"]:
        if str(concepto).startswith(f"{codigo_resuelto} - "):
            return str(concepto)
    return None


def _redondear_significativo(valor, cifras=6):
    """Redondea por cifras significativas: un valor > 0 jamás se vuelve 0.0."""
    if valor == 0:
        return 0.0
    return float(f"{float(valor):.{cifras}g}")


def _crear_lista_enriquecida(temp_df, top_n):
    """
    Construye el top de sectores relacionados con filtrado estricto.

    - Solo coeficientes técnicos > 0 (prohibido rellenar con ceros).
    - "porcentaje" / "participacion_relativa": peso del coeficiente
      dentro del total de coeficientes positivos del flujo (0-100).
    """
    temp_df = temp_df[temp_df["sector"].str.match(r"^\d")]
    temp_df = temp_df.dropna(subset=["coeficiente"])
    temp_df = temp_df[temp_df["coeficiente"] > 0]

    total_positivo = float(temp_df["coeficiente"].sum())
    if total_positivo <= 0:
        return []

    top = temp_df.sort_values("coeficiente", ascending=False).head(top_n)

    resultado = []
    for _, row in top.iterrows():
        codigo = _extraer_codigo(row["sector"])
        participacion = float(row["coeficiente"]) / total_positivo * 100

        resultado.append({
            "codigo": codigo,
            "sector": row["sector"],
            "categoria": obtener_categoria(codigo),
            "coeficiente": _redondear_significativo(row["coeficiente"]),
            # Cifras significativas: una relación real jamás se muestra como 0.0
            "porcentaje": _redondear_significativo(participacion),
            "participacion_relativa": _redondear_significativo(participacion),
        })
    return resultado


def analizar_sector(codigo_scian, top_n=TOP_N_DEFAULT):
    """
    Genera las recomendaciones sectoriales de un código SCIAN.

    Returns:
        dict con la resolución trazable y los tops de clientes y
        proveedores (solo coeficientes > 0), o None si el código no
        tiene equivalencia en la MIP.

    Raises:
        CodigoInvalidoError: si el formato del código es inválido.
    """
    df = cargar_mip()

    resolucion = resolver_codigo_mip(codigo_scian, _codigos_mip(df))
    if resolucion is None:
        return None

    codigo_resuelto = resolucion.codigo_resuelto
    nombre_columna = _nombre_sector(df, codigo_resuelto)
    nombre_fila = nombre_columna
    if nombre_columna is None:
        return None

    categoria_principal = obtener_categoria(codigo_resuelto)

    # Clientes: fila del sector (quiénes le compran / usan su producto)
    fila_sector = df[df["Concepto"] == nombre_fila].iloc[0]
    fila_valores = pd.to_numeric(fila_sector.drop("Concepto"), errors="coerce")

    temp_clientes = pd.DataFrame({
        "sector": fila_valores.index,
        "coeficiente": fila_valores.values
    })
    lista_clientes = _crear_lista_enriquecida(temp_clientes, top_n)

    # Proveedores: columna del sector (de quiénes compra insumos)
    columna_valores = pd.to_numeric(df[nombre_columna], errors="coerce")
    temp_proveedores = pd.DataFrame({
        "sector": df["Concepto"].values,
        "coeficiente": columna_valores.values
    })
    lista_proveedores = _crear_lista_enriquecida(temp_proveedores, top_n)

    return {
        "codigo": resolucion.codigo_buscado,
        "codigo_buscado": resolucion.codigo_buscado,
        "codigo_resuelto": codigo_resuelto,
        "codigo_mip": codigo_resuelto,
        "metodo_mapeo": resolucion.metodo_mapeo,
        "nivel_agregacion": resolucion.nivel_agregacion,
        "sector": nombre_fila,
        "categoria": categoria_principal,
        "top_clientes": lista_clientes,
        "top_proveedores": lista_proveedores
    }


def listar_sectores():
    df = cargar_mip()
    sectores = []
    for concepto in df["Concepto"]:
        codigo = _extraer_codigo(concepto)
        if codigo and codigo.isdigit():
            sectores.append({"codigo": codigo, "nombre": concepto})
    return sectores

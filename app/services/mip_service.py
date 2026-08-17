"""
==========================================
MIP SERVICE
==========================================
Servicio para analizar la Matriz Insumo-Producto 2013
y generar recomendaciones de proveedores/clientes.
"""

import pandas as pd
from app.core.config import RUTA_MIP, FILA_ENCABEZADOS_MIP, TOP_N_DEFAULT
from app.services.clasificacion_service import obtener_categoria


# ==========================================
# CACHE GLOBAL DE LA MIP
# ==========================================
_mip_cache = None


# ==========================================
# CARGAR MIP
# ==========================================
def cargar_mip():
    """
    Carga la MIP desde el Excel, limpia los datos y la guarda en cache.

    Returns:
        pd.DataFrame: DataFrame limpio con la matriz
    """
    global _mip_cache

    if _mip_cache is not None:
        return _mip_cache

    df = pd.read_excel(RUTA_MIP, header=FILA_ENCABEZADOS_MIP)

    # Limpieza
    df = df[df["Concepto"].notna()]
    df = df[~df["Concepto"].str.startswith("Fuente:", na=False)]
    df["Concepto"] = df["Concepto"].str.strip()
    df.columns = [str(col).strip() for col in df.columns]

    _mip_cache = df
    return df


# ==========================================
# HELPERS
# ==========================================
def _extraer_codigo(texto_sector):
    """Extrae el código SCIAN de '1111 - Cultivo...' → '1111'"""
    partes = texto_sector.strip().split(" - ")
    return partes[0].strip() if partes else None


def _buscar_columna(df, codigo):
    """Busca la columna que empieza con el código."""
    for col in df.columns:
        if str(col).startswith(f"{codigo} "):
            return col
    return None


def _buscar_fila(df, codigo):
    """Busca la fila (concepto) que empieza con el código."""
    for concepto in df["Concepto"]:
        if str(concepto).startswith(f"{codigo} "):
            return concepto
    return None


def _crear_lista_enriquecida(temp_df, top_n):
    """
    Convierte un DataFrame temporal en lista de diccionarios
    con categoría incluida.
    """
    # Filtrar solo sectores reales (que empiecen con dígito)
    temp_df = temp_df[temp_df["sector"].str.match(r"^\d")]

    # Top N
    top = temp_df.sort_values("coeficiente", ascending=False).head(top_n)

    resultado = []
    for _, row in top.iterrows():
        codigo = _extraer_codigo(row["sector"])
        categoria = obtener_categoria(codigo)

        resultado.append({
            "codigo": codigo,
            "sector": row["sector"],
            "categoria": categoria,
            "coeficiente": round(float(row["coeficiente"]), 6),
            "porcentaje": round(float(row["coeficiente"]) * 100, 2)
        })

    return resultado


# ==========================================
# ANALIZAR SECTOR (FUNCIÓN PRINCIPAL)
# ==========================================
def analizar_sector(codigo_scian, top_n=TOP_N_DEFAULT):
    """
    Analiza un sector y devuelve sus top clientes/proveedores
    con categorías incluidas.

    Args:
        codigo_scian (str): Código SCIAN a analizar
        top_n (int): Cantidad de resultados por categoría

    Returns:
        dict: Información completa del sector, o None si no existe
    """
    df = cargar_mip()

    # Buscar sector
    nombre_columna = _buscar_columna(df, codigo_scian)
    nombre_fila = _buscar_fila(df, codigo_scian)

    if not nombre_columna or not nombre_fila:
        return None

    # Categoría del sector principal
    categoria_principal = obtener_categoria(codigo_scian)

    # ---------- CLIENTES (fila) ----------
    fila_sector = df[df["Concepto"] == nombre_fila].iloc[0]
    fila_valores = fila_sector.drop("Concepto")
    fila_valores = pd.to_numeric(fila_valores, errors="coerce")

    temp_clientes = pd.DataFrame({
        "sector": fila_valores.index,
        "coeficiente": fila_valores.values
    })
    lista_clientes = _crear_lista_enriquecida(temp_clientes, top_n)

    # ---------- PROVEEDORES (columna) ----------
    columna_valores = pd.to_numeric(df[nombre_columna], errors="coerce")
    temp_proveedores = pd.DataFrame({
        "sector": df["Concepto"].values,
        "coeficiente": columna_valores.values
    })
    lista_proveedores = _crear_lista_enriquecida(temp_proveedores, top_n)

    # ---------- RESULTADO ----------
    return {
        "codigo": codigo_scian,
        "sector": nombre_fila,
        "categoria": categoria_principal,
        "top_clientes": lista_clientes,
        "top_proveedores": lista_proveedores
    }


# ==========================================
# LISTAR TODOS LOS SECTORES
# ==========================================
def listar_sectores():
    """
    Devuelve una lista de todos los sectores disponibles en la MIP.

    Returns:
        list: [{"codigo": "1111", "nombre": "Cultivo..."}, ...]
    """
    df = cargar_mip()
    sectores = []

    for concepto in df["Concepto"]:
        codigo = _extraer_codigo(concepto)
        if codigo and codigo.isdigit():  # Solo sectores reales
            sectores.append({
                "codigo": codigo,
                "nombre": concepto
            })

    return sectores
"""

mip service (actualizado con cascada jerarquica)

servicio para analizar la Matriz Insumo-Producto 2013
y generar recomendaciones de proveedores o clientes

"""

import pandas as pd
from app.core.config import RUTA_MIP, FILA_ENCABEZADOS_MIP, TOP_N_DEFAULT
from app.services.clasificacion_service import obtener_categoria

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

def _encontrar_codigo_mip(df, codigo_original):
    """
    Busca un codigo. Si es de 6 dígitos (311811) y no existe, 
    busca el de 5 (31181), luego el de 4 (3118), luego el de 3 (311).
    """
    codigo = str(codigo_original).strip()

    while len(codigo) >= 3:
        col_encontrada = None
        fila_encontrada = None

        # Buscar en columnas
        for col in df.columns:
            if str(col).startswith(f"{codigo} ") or str(col) == codigo:
                col_encontrada = col
                break

        # Buscar en filas (Concepto)
        for concepto in df["Concepto"]:
            if str(concepto).startswith(f"{codigo} ") or str(concepto) == codigo:
                fila_encontrada = concepto
                break

        # Si encontro ambos, devolvemos el match
        if col_encontrada and fila_encontrada:
            return codigo, col_encontrada, fila_encontrada

        # Si no encontro, le quitamos el ultimo digito y volvemos a intentar
        codigo = codigo[:-1]

    return None, None, None

def _crear_lista_enriquecida(temp_df, top_n):
    temp_df = temp_df[temp_df["sector"].str.match(r"^\d")]
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

def analizar_sector(codigo_scian, top_n=TOP_N_DEFAULT):
    df = cargar_mip()

    # Usar el nuevo buscador inteligente con cascada
    codigo_resuelto, nombre_columna, nombre_fila = _encontrar_codigo_mip(df, codigo_scian)

    if not codigo_resuelto:
        return None

    categoria_principal = obtener_categoria(codigo_resuelto)

    # clientes (fila) 
    fila_sector = df[df["Concepto"] == nombre_fila].iloc[0]
    fila_valores = fila_sector.drop("Concepto")
    fila_valores = pd.to_numeric(fila_valores, errors="coerce")

    temp_clientes = pd.DataFrame({
        "sector": fila_valores.index,
        "coeficiente": fila_valores.values
    })
    lista_clientes = _crear_lista_enriquecida(temp_clientes, top_n)

    # proveedores (columna)
    columna_valores = pd.to_numeric(df[nombre_columna], errors="coerce")
    temp_proveedores = pd.DataFrame({
        "sector": df["Concepto"].values,
        "coeficiente": columna_valores.values
    })
    lista_proveedores = _crear_lista_enriquecida(temp_proveedores, top_n)

    # resultado
    return {
        "codigo": codigo_scian,                   # Mantiene compatibilidad
        "codigo_buscado": codigo_scian,           # Ej: 311811
        "codigo_resuelto": codigo_resuelto,       # Ej: 3118
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
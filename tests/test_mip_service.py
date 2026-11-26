"""Tests del servicio de análisis MIP (reglas analíticas estrictas)."""
import pytest

from app.services.codigo_service import CodigoInvalidoError
from app.services.mip_service import analizar_sector, listar_sectores


def test_listar_sectores_devuelve_262_ramas():
    sectores = listar_sectores()
    assert len(sectores) == 262
    assert all(s["codigo"].isdigit() and len(s["codigo"]) == 4 for s in sectores)


def test_sector_exacto_trazable():
    r = analizar_sector("3118")
    assert r["codigo_resuelto"] == "3118"
    assert r["codigo_mip"] == "3118"
    assert r["metodo_mapeo"] == "exacto"


def test_clase_6_digitos_se_agrega_a_su_rama():
    r = analizar_sector("311811")
    assert r["codigo_buscado"] == "311811"
    assert r["codigo_resuelto"] == "3118"
    assert r["metodo_mapeo"] == "padre_jerarquico"


def test_codigo_comercial_huerfano_usa_crosswalk():
    r = analizar_sector("4659")
    assert r is not None
    assert r["codigo_resuelto"] == "4611"
    assert r["metodo_mapeo"] == "agregacion_comercial"


def test_codigo_sin_equivalencia_devuelve_none():
    assert analizar_sector("9999") is None


def test_formato_invalido_lanza_excepcion():
    with pytest.raises(CodigoInvalidoError):
        analizar_sector("46-59")


@pytest.mark.parametrize("codigo", ["3111", "3118", "4611", "8132", "1142", "525210"])
def test_nunca_relaciones_con_coeficiente_cero(codigo):
    """Regla dura: prohibido emitir relaciones ficticias con coeficiente <= 0."""
    r = analizar_sector(codigo, top_n=20)
    assert r is not None
    for nodo in r["top_clientes"] + r["top_proveedores"]:
        assert nodo["coeficiente"] > 0
        assert nodo["participacion_relativa"] > 0


def test_sector_sin_clientes_reales_no_rellena_con_ceros():
    """8132 tenía su fila en cero: antes devolvía cultivos con 0.0."""
    r = analizar_sector("8132", top_n=5)
    assert r["top_clientes"] == []
    assert len(r["top_proveedores"]) > 0


def test_porcentaje_es_participacion_normalizada():
    """El porcentaje ya no es el coeficiente bruto x 100: debe sumar ~100."""
    r = analizar_sector("3111", top_n=20)
    for clave in ("top_clientes", "top_proveedores"):
        suma = sum(n["porcentaje"] for n in r[clave])
        assert 0 < suma <= 100.5  # 100 + tolerancia por redondeo a 6 cifras
        for nodo in r[clave]:
            assert nodo["porcentaje"] == nodo["participacion_relativa"]

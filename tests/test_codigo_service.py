"""Tests de la resolución centralizada de códigos SCIAN -> MIP."""
import pytest

from app.services.codigo_service import (
    CodigoInvalidoError,
    cargar_crosswalk,
    normalizar_codigo,
    resolver_codigo_mip,
)
from app.services.mip_service import cargar_mip, _codigos_mip


@pytest.fixture(scope="module")
def codigos_mip():
    return _codigos_mip(cargar_mip())


class TestNormalizarCodigo:
    def test_acepta_rama_de_4_digitos(self):
        assert normalizar_codigo("3118") == "3118"
        assert normalizar_codigo(3118) == "3118"

    def test_acepta_clase_de_6_digitos(self):
        assert normalizar_codigo("311811") == "311811"

    def test_tolera_espacios_y_sufijo_excel(self):
        assert normalizar_codigo(" 3118 ") == "3118"
        assert normalizar_codigo("3118.0") == "3118"

    @pytest.mark.parametrize("invalido", ["46-59", "46 59", "", "abcd", "31181", "311", "03118"])
    def test_rechaza_formatos_invalidos(self, invalido):
        with pytest.raises(CodigoInvalidoError):
            normalizar_codigo(invalido)


class TestCrosswalk:
    def test_carga_equivalencias_sin_duplicados(self):
        crosswalk = cargar_crosswalk()
        assert len(crosswalk) == 30
        assert crosswalk["4659"]["codigo_mip"] == "4611"
        assert crosswalk["2213"]["codigo_mip"] == "2221"


class TestResolverCodigoMip:
    def test_exacto(self, codigos_mip):
        r = resolver_codigo_mip("3118", codigos_mip)
        assert r.codigo_resuelto == "3118"
        assert r.metodo_mapeo == "exacto"

    def test_padre_jerarquico(self, codigos_mip):
        r = resolver_codigo_mip("311811", codigos_mip)
        assert r.codigo_resuelto == "3118"
        assert r.metodo_mapeo == "padre_jerarquico"

    def test_crosswalk_codigo_empresa_huerfano(self, codigos_mip):
        r = resolver_codigo_mip("4659", codigos_mip)
        assert r.codigo_resuelto == "4611"
        assert r.metodo_mapeo == "agregacion_comercial"

    def test_crosswalk_no_articulado_6_digitos(self, codigos_mip):
        r = resolver_codigo_mip("437111", codigos_mip)
        assert r.codigo_resuelto == "4311"

    def test_sin_equivalencia_devuelve_none(self, codigos_mip):
        assert resolver_codigo_mip("9999", codigos_mip) is None
        assert resolver_codigo_mip("5858", codigos_mip) is None

    def test_formato_invalido_lanza_422(self, codigos_mip):
        with pytest.raises(CodigoInvalidoError):
            resolver_codigo_mip("46-59", codigos_mip)

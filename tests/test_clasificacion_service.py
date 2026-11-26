"""Tests del servicio de clasificación estratégica."""
import pytest

from app.services.codigo_service import CodigoInvalidoError
from app.services.clasificacion_service import (
    obtener_categoria,
    obtener_conflictos,
    obtener_estadisticas,
)


def test_categoria_exacta():
    assert obtener_categoria("3118") == "ARTICULADOS GRISES"


def test_categoria_heredada_de_rama_padre():
    # 311811 no está en la clasificación; hereda la de 3118
    assert obtener_categoria("311811") == obtener_categoria("3118")


def test_categoria_no_articulado_6_digitos():
    assert obtener_categoria("525210") == "NO ARTICULADO"


def test_sector_mip_sin_clasificar():
    # 9313 existe en la MIP pero en ninguna hoja de categorías
    assert obtener_categoria("9313") == "Sin clasificar"


def test_formato_invalido_lanza_excepcion():
    with pytest.raises(CodigoInvalidoError):
        obtener_categoria("46-59")


def test_estadisticas_solo_cuentan_codigos_validos():
    """Las notas/encabezados dentro de las hojas ya no inflan el total."""
    stats = obtener_estadisticas()
    assert stats["total"] == 316
    assert sum(stats["por_categoria"].values()) == 316


def test_conflictos_entre_hojas_quedan_registrados():
    conflictos = obtener_conflictos()
    codigos = {c["codigo"] for c in conflictos}
    assert "3241" in codigos  # Clave + Articulador + ARTICULADOS GRISES
    assert "3111" in codigos  # Clave + Articulador

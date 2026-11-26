"""Tests HTTP del directorio empresarial y del emparejamiento de socios."""
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_directorio_empresarial_paginado(client):
    r = client.get("/empresas", params={"limite": 5})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["total"] == 238943
    assert len(cuerpo["empresas"]) == 5
    assert cuerpo["empresas"][0]["codigo_scian"]


def test_directorio_filtra_por_codigo(client):
    r = client.get("/empresas", params={"codigo_scian": "4659", "limite": 3})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["total"] == 52006
    # Todas homologadas vía crosswalk a la rama 4611
    assert all(e["codigo_mip"] == "4611" for e in cuerpo["empresas"])


def test_directorio_codigo_invalido_es_422(client):
    r = client.get("/empresas", params={"codigo_scian": "46-59"})
    assert r.status_code == 422
    assert r.json()["detail"]["causa"] == "formato_invalido"


def test_socios_devuelve_empresas_reales(client):
    r = client.get("/empresas/socios/3119", params={"top_n": 3, "por_sector": 2})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["codigo_resuelto"] == "3119"
    grupos = cuerpo["socios_clientes"] + cuerpo["socios_proveedores"]
    assert grupos, "Debe haber sectores relacionados"
    for grupo in grupos:
        assert grupo["coeficiente"] > 0
        assert grupo["total_empresas"] >= len(grupo["empresas"])
        for empresa in grupo["empresas"]:
            assert empresa["codigo_mip"] == grupo["codigo"]
            assert empresa["registro_id"] > 1


def test_socios_para_el_codigo_con_mas_empresas(client):
    """4659 concentra 52,006 empresas y antes devolvía 404 en todo."""
    r = client.get("/empresas/socios/4659", params={"top_n": 3, "por_sector": 2})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["codigo_resuelto"] == "4611"
    assert cuerpo["metodo_mapeo"] == "agregacion_comercial"
    total_socios = sum(
        g["total_empresas"] for g in cuerpo["socios_clientes"] + cuerpo["socios_proveedores"]
    )
    assert total_socios > 0


def test_socios_sin_equivalencia_es_404_estructurado(client):
    r = client.get("/empresas/socios/9999")
    assert r.status_code == 404
    assert r.json()["detail"]["causa"] == "sin_equivalencia_mip"


def test_socios_formato_invalido_es_422(client):
    r = client.get("/empresas/socios/46-59")
    assert r.status_code == 422
    assert r.json()["detail"]["causa"] == "formato_invalido"

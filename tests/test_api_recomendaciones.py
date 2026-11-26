"""Tests HTTP de los endpoints de recomendaciones (consistencia total)."""
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ambos_endpoints_resuelven_igual_una_clase_6_digitos(client):
    """Antes: /sector/311811 daba 404 y /311811 daba 200. Deben coincidir."""
    info = client.get("/recomendaciones/sector/311811")
    completa = client.get("/recomendaciones/311811")
    assert info.status_code == 200
    assert completa.status_code == 200
    assert info.json()["codigo_resuelto"] == "3118"
    assert completa.json()["codigo_resuelto"] == "3118"
    assert completa.json()["metodo_mapeo"] == "padre_jerarquico"


def test_sector_con_crosswalk_responde_200(client):
    r = client.get("/recomendaciones/sector/4659")
    assert r.status_code == 200
    assert r.json()["codigo_resuelto"] == "4611"


def test_recomendaciones_con_crosswalk_responden_200(client):
    r = client.get("/recomendaciones/4659")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["codigo_mip"] == "4611"
    assert all(n["coeficiente"] > 0 for n in cuerpo["top_clientes"] + cuerpo["top_proveedores"])


def test_sin_equivalencia_es_404_estructurado(client):
    r = client.get("/recomendaciones/9999")
    assert r.status_code == 404
    detalle = r.json()["detail"]
    assert detalle["causa"] == "sin_equivalencia_mip"
    assert detalle["codigo"] == "9999"


def test_formato_invalido_es_422_estructurado(client):
    for ruta in ("/recomendaciones/46-59", "/recomendaciones/sector/46-59"):
        r = client.get(ruta)
        assert r.status_code == 422, ruta
        assert r.json()["detail"]["causa"] == "formato_invalido"


def test_codigo_de_5_digitos_es_422(client):
    r = client.get("/recomendaciones/sector/31181")
    assert r.status_code == 422


def test_sector_sin_clientes_reales_lista_vacia(client):
    r = client.get("/recomendaciones/8132")
    assert r.status_code == 200
    assert r.json()["top_clientes"] == []

"""Smoke tests that run with zero external services (no Ollama needed)."""
from fastapi.testclient import TestClient

from openbay.coordinator.app import app


def test_root_ok():
    c = TestClient(app)
    r = c.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "openbay-coordinator"


def test_register_then_listed():
    c = TestClient(app)
    r = c.post(
        "/register",
        json={"node_id": "n1", "url": "http://localhost:9000",
              "models": ["llama3.2"]},
    )
    assert r.status_code == 200
    nodes = c.get("/nodes").json()
    assert any(n["node_id"] == "n1" for n in nodes)


def test_infer_without_seeder_returns_503():
    c = TestClient(app)
    r = c.post("/v1/infer", json={"model": "no-such-model", "prompt": "hi"})
    assert r.status_code == 503

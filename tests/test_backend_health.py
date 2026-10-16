from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_root_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"

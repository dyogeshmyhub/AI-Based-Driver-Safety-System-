from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.monitoring_service import monitoring_service


class FakeMonitor:
    def __init__(self):
        self.running = False
        self.state = {
            "timestamp": "2026-09-25T00:00:00+00:00",
            "monitoring": False,
            "camera": {"status": "offline", "resolution": "0x0", "fps": 0},
            "face": {"detected": False, "faces": 0},
            "eyes": {"left_ear": 0.0, "right_ear": 0.0, "average_ear": 0.0, "status": "OPEN", "blink_count": 0},
            "mouth": {"status": "CLOSED", "yawn_count": 0},
            "head": {"direction": "FORWARD"},
            "attention": {"status": "ATTENTIVE"},
            "drowsiness": {"status": "ALERT"},
            "safety": {"score": 100, "risk_level": "LOW", "active_risks": []},
            "alert": {"level": "INFO", "message": "Monitoring is stopped.", "alarm_active": False},
            "session": {"active": False, "duration_seconds": 0, "alerts": 0, "average_score": 100.0, "minimum_score": 100.0, "drowsiness_events": 0, "yawns": 0},
            "error": None,
        }

    def start(self):
        self.running = True
        self.state["monitoring"] = True
        return True

    def stop(self):
        self.running = False
        self.state["monitoring"] = False
        return True

    def snapshot(self):
        return self.state


class FakeService:
    def __init__(self, real_service):
        self.fake = FakeMonitor()
        self.repository = real_service.repository

    def start(self):
        return self.fake.start()

    def stop(self):
        return self.fake.stop()

    def is_running(self):
        return self.fake.running

    def snapshot(self):
        return self.fake.snapshot()


def test_phase6_health_and_monitoring_api(monkeypatch):
    fake_service = FakeService(monitoring_service)
    monkeypatch.setattr("backend.api.routes.monitoring_service", fake_service)
    monkeypatch.setattr("backend.api.websocket.monitoring_service", fake_service)
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "ok", "service": "driver-safety-api", "version": "1.0.0"}
        status = client.get("/api/monitoring/status")
        assert status.status_code == 200
        assert status.json()["safety"]["score"] == 100
        assert client.post("/api/monitoring/start").json()["success"] is True
        assert client.post("/api/monitoring/start").json()["message"] == "Monitoring is already running"
        assert client.post("/api/monitoring/stop").json()["success"] is True


def test_phase6_websocket_sends_monitoring_update(monkeypatch):
    fake_service = FakeService(monitoring_service)
    monkeypatch.setattr("backend.api.websocket.monitoring_service", fake_service)
    with TestClient(app) as client:
        with client.websocket_connect("/ws/monitoring") as websocket:
            payload = websocket.receive_json()
            assert payload["type"] == "monitoring_update"
            assert payload["connected"] is True
            assert payload["monitoring"] is False
            assert payload["camera"]["online"] is False
            assert payload["safety"]["risk_level"] == "LOW"


def test_phase6_monitoring_contract_has_live_fields(monkeypatch):
    fake_service = FakeService(monitoring_service)
    monkeypatch.setattr("backend.api.routes.monitoring_service", fake_service)
    with TestClient(app) as client:
        response = client.get("/api/monitoring/status")
        assert response.status_code == 200
        payload = response.json()
        assert "connected" in payload
        assert payload["camera"]["online"] is False
        assert payload["camera"]["width"] == 0
        assert payload["camera"]["height"] == 0
        assert payload["driver"]["eyes"] == "OPEN"
        assert payload["driver"]["head_pose"] == "FORWARD"

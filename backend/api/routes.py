from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from backend.schemas.monitoring import ActionResponse, EventResponse, HealthResponse, MonitoringState, SessionResponse
from backend.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/api")


def _state_payload() -> dict:
    state = monitoring_service.snapshot()
    camera = state.get("camera", {})
    driver = state.get("driver", {})
    safety = state.get("safety", {})
    return {
        "connected": bool(state.get("connected", True)),
        "timestamp": state.get("timestamp"),
        "monitoring": bool(state.get("monitoring", False)),
        "camera": {
            "online": bool(camera.get("online", camera.get("status") == "online")),
            "status": camera.get("status", "offline"),
            "width": int(camera.get("width", 0)),
            "height": int(camera.get("height", 0)),
            "resolution": camera.get("resolution", "0x0"),
            "fps": int(camera.get("fps", 0)),
        },
        "driver": {
            "face_detected": bool(driver.get("face_detected", state.get("face", {}).get("detected", False))),
            "faces": int(driver.get("faces", state.get("face", {}).get("faces", 0))),
            "eyes": driver.get("eyes", state.get("eyes", {}).get("status", "OPEN")),
            "left_ear": float(driver.get("left_ear", state.get("eyes", {}).get("left_ear", 0.0))),
            "right_ear": float(driver.get("right_ear", state.get("eyes", {}).get("right_ear", 0.0))),
            "average_ear": float(driver.get("average_ear", state.get("eyes", {}).get("average_ear", 0.0))),
            "blink_count": int(driver.get("blink_count", state.get("eyes", {}).get("blink_count", 0))),
            "mouth": driver.get("mouth", state.get("mouth", {}).get("status", "CLOSED")),
            "yawn_count": int(driver.get("yawn_count", state.get("mouth", {}).get("yawn_count", 0))),
            "head_pose": driver.get("head_pose", state.get("head", {}).get("direction", "FORWARD")),
            "attention": driver.get("attention", state.get("attention", {}).get("status", "ATTENTIVE")),
            "drowsiness": driver.get("drowsiness", state.get("drowsiness", {}).get("status", "ALERT")),
        },
        "safety": {
            "score": int(safety.get("score", state.get("safety", {}).get("score", 100))),
            "risk_level": safety.get("risk_level", state.get("safety", {}).get("risk_level", "LOW")),
            "status": safety.get("status", "SAFE" if safety.get("risk_level") in {"LOW", "MEDIUM"} else "WARNING"),
            "active_risks": list(safety.get("active_risks", state.get("safety", {}).get("active_risks", []))),
        },
        "alert": state.get("alert", {"level": "INFO", "message": "Monitoring is stopped.", "alarm_active": False}),
        "session": state.get("session", {"active": False, "duration_seconds": 0}),
        "error": state.get("error"),
    }


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="driver-safety-api", version="1.0.0")


@router.get("/monitoring/status", response_model=MonitoringState)
def monitoring_status() -> MonitoringState:
    return MonitoringState.model_validate(_state_payload())


@router.post("/monitoring/start", response_model=ActionResponse)
def start_monitoring() -> ActionResponse:
    if monitoring_service.is_running():
        return ActionResponse(success=True, message="Monitoring is already running")
    if not monitoring_service.start():
        state = monitoring_service.snapshot()
        return ActionResponse(success=False, message=state.get("error") or "Camera unavailable")
    return ActionResponse(success=True, message="Monitoring started")


@router.post("/monitoring/stop", response_model=ActionResponse)
def stop_monitoring() -> ActionResponse:
    monitoring_service.stop()
    return ActionResponse(success=True, message="Monitoring stopped")


@router.get("/camera/frame")
def camera_frame() -> Response:
    frame = monitoring_service.get_camera_frame()
    if frame is None:
        return Response(status_code=204, content=b"")
    return Response(content=frame, media_type="image/jpeg")


def _session_response(session) -> SessionResponse:
    return SessionResponse(**session.to_dict())


def _event_response(event) -> EventResponse:
    return EventResponse(**event.to_dict())


@router.get("/sessions", response_model=list[SessionResponse])
def sessions() -> list[SessionResponse]:
    return [_session_response(item) for item in monitoring_service.repository.get_recent_sessions()]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def session(session_id: str) -> SessionResponse:
    item = monitoring_service.repository.get_session(session_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_response(item)


@router.get("/sessions/{session_id}/events", response_model=list[EventResponse])
def session_events(session_id: str) -> list[EventResponse]:
    if monitoring_service.repository.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return [_event_response(item) for item in monitoring_service.repository.get_events(session_id)]


@router.delete("/sessions/{session_id}", response_model=ActionResponse)
def delete_session(session_id: str) -> ActionResponse:
    if monitoring_service.repository.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    monitoring_service.repository.delete_session(session_id)
    return ActionResponse(success=True, message="Session deleted")


@router.get("/events/recent", response_model=list[EventResponse])
def recent_events() -> list[EventResponse]:
    return [_event_response(item) for item in monitoring_service.repository.get_recent_events()]

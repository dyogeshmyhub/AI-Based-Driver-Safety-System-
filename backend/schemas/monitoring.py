from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ActionResponse(BaseModel):
    success: bool
    message: str


class CameraState(BaseModel):
    online: bool = False
    status: str = "offline"
    width: int = 0
    height: int = 0
    resolution: str = "0x0"
    fps: int = 0


class DriverState(BaseModel):
    face_detected: bool = False
    faces: int = 0
    eyes: str = "OPEN"
    left_ear: float = 0.0
    right_ear: float = 0.0
    average_ear: float = 0.0
    blink_count: int = 0
    mouth: str = "CLOSED"
    yawn_count: int = 0
    head_pose: str = "FORWARD"
    attention: str = "ATTENTIVE"
    drowsiness: str = "ALERT"


class SafetyState(BaseModel):
    score: int = 100
    risk_level: str = "LOW"
    status: str = "SAFE"
    active_risks: list[str] = []


class MonitoringState(BaseModel):
    connected: bool = True
    timestamp: str
    monitoring: bool
    camera: CameraState
    driver: DriverState
    safety: SafetyState
    face: dict[str, Any] | None = None
    eyes: dict[str, Any] | None = None
    mouth: dict[str, Any] | None = None
    head: dict[str, Any] | None = None
    attention: dict[str, Any] | None = None
    drowsiness: dict[str, Any] | None = None
    alert: dict[str, Any] | None = None
    session: dict[str, Any] | None = None
    error: str | None = None


class SessionResponse(BaseModel):
    id: str
    start_time: str
    end_time: str | None
    duration: float
    average_safety_score: float
    minimum_safety_score: float
    maximum_risk_level: str
    total_alerts: int
    total_drowsiness_events: int
    total_yawns: int
    total_blinks: int


class EventResponse(BaseModel):
    id: str
    session_id: str | None
    timestamp: str
    event_type: str
    severity: str
    safety_score: int
    risk_level: str
    message: str
    metadata: dict[str, Any] | None = None

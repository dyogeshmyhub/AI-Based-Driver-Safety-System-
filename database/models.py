from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class SessionRecord:
    id: str
    start_time: str
    end_time: str | None = None
    duration: float = 0.0
    average_safety_score: float = 0.0
    minimum_safety_score: float = 100.0
    maximum_risk_level: str = "LOW"
    total_alerts: int = 0
    total_drowsiness_events: int = 0
    total_yawns: int = 0
    total_blinks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyEventRecord:
    id: str
    session_id: str
    timestamp: str
    event_type: str
    severity: str
    safety_score: int
    risk_level: str
    message: str
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

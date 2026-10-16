from __future__ import annotations

from ai.config import CRITICAL_EYE_CLOSED_DURATION, DROWSY_EYE_CLOSED_DURATION, WARNING_EYE_CLOSED_DURATION


class DrowsinessDetector:
    """Simple drowsiness state machine based on sustained eye closure."""

    def __init__(
        self,
        drowsy_duration: float = DROWSY_EYE_CLOSED_DURATION,
        critical_duration: float = CRITICAL_EYE_CLOSED_DURATION,
        warning_duration: float = WARNING_EYE_CLOSED_DURATION,
    ):
        self.drowsy_duration = drowsy_duration
        self.critical_duration = critical_duration
        self.warning_duration = warning_duration

        self.state = "ALERT"
        self.eye_status = "OPEN"
        self.eye_closed_duration = 0.0

    def update(
        self,
        average_ear: float = 0.0,
        eye_closed_duration: float | None = None,
        frame_count: int | None = None,
    ) -> dict:
        """Return a structured status payload for the current eye state."""
        if eye_closed_duration is None:
            eye_closed_duration = float(average_ear) if average_ear > 0 else 0.0

        self.eye_closed_duration = float(eye_closed_duration)

        if self.eye_closed_duration <= 0.1:
            self.eye_status = "OPEN"
            self.state = "ALERT"
        elif self.eye_closed_duration < self.warning_duration:
            self.eye_status = "CLOSED"
            self.state = "WARNING"
        elif self.eye_closed_duration < self.drowsy_duration:
            self.eye_status = "CLOSED"
            self.state = "DROWSY"
        else:
            self.eye_status = "CLOSED"
            self.state = "CRITICAL"

        return {
            "state": self.state,
            "eye_status": self.eye_status,
            "ear": float(average_ear),
            "left_ear": float(average_ear),
            "right_ear": float(average_ear),
            "blink_count": 0,
            "eye_closed_duration": float(self.eye_closed_duration),
            "drowsiness_detected": self.state in {"WARNING", "DROWSY", "CRITICAL"},
        }

    def reset(self):
        self.state = "ALERT"
        self.eye_status = "OPEN"
        self.eye_closed_duration = 0.0


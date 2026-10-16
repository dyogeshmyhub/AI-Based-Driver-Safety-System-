from __future__ import annotations

from typing import Any

from ai.config import MOUTH_OPEN_THRESHOLD, YAWN_COOLDOWN, YAWN_MIN_DURATION


class YawnDetector:
    """Track mouth openness and detect yawns using a duration-based state machine."""

    def __init__(
        self,
        mouth_open_threshold: float = MOUTH_OPEN_THRESHOLD,
        yawn_min_duration: float = YAWN_MIN_DURATION,
        yawn_cooldown: float = YAWN_COOLDOWN,
    ) -> None:
        self.mouth_open_threshold = mouth_open_threshold
        self.yawn_min_duration = yawn_min_duration
        self.yawn_cooldown = yawn_cooldown

        self.mouth_open_value = 0.0
        self.mouth_state = "MOUTH CLOSED"
        self.yawn_state = "MOUTH CLOSED"
        self.yawn_start_time: float | None = None
        self.yawn_duration = 0.0
        self.yawn_count = 0
        self.last_yawn_time: float | None = None
        self._open_start_time: float | None = None
        self._is_yawn_in_progress = False
        self._synthetic_time = 0.0

    def _classify_mouth(self, mouth_ratio: float) -> str:
        if mouth_ratio <= 0:
            return "MOUTH CLOSED"
        return "MOUTH OPEN" if mouth_ratio >= self.mouth_open_threshold else "MOUTH CLOSED"

    def update(self, mouth_ratio: float, timestamp: float | None = None) -> dict[str, Any]:
        if timestamp is None:
            self._synthetic_time += 1.0 / 30.0
            timestamp = self._synthetic_time

        timestamp = float(timestamp)
        self.mouth_open_value = float(mouth_ratio)
        previous_state = self.mouth_state
        self.mouth_state = self._classify_mouth(self.mouth_open_value)

        if self.mouth_state == "MOUTH OPEN":
            if self._open_start_time is None:
                self._open_start_time = timestamp
            self.yawn_duration = max(0.0, timestamp - self._open_start_time)
            if self.yawn_start_time is None:
                self.yawn_start_time = timestamp
            if self.yawn_duration >= self.yawn_min_duration:
                if not self._is_yawn_in_progress:
                    if self.last_yawn_time is None or (timestamp - self.last_yawn_time) >= self.yawn_cooldown:
                        self.yawn_count += 1
                        self.last_yawn_time = timestamp
                        self._is_yawn_in_progress = True
                self.yawn_state = "YAWN DETECTED"
            else:
                self.yawn_state = "YAWN SUSPECTED"
        else:
            self.yawn_duration = 0.0
            self._open_start_time = None
            self.yawn_start_time = None
            self._is_yawn_in_progress = False
            self.yawn_state = "MOUTH CLOSED"

        if previous_state == "MOUTH OPEN" and self.mouth_state == "MOUTH CLOSED":
            self.yawn_state = "MOUTH CLOSED"

        yawn_detected = self.yawn_state == "YAWN DETECTED"
        return {
            "mouth_state": self.mouth_state,
            "mouth_open_value": self.mouth_open_value,
            "yawn_state": self.yawn_state,
            "yawn_start_time": self.yawn_start_time,
            "yawn_duration": self.yawn_duration,
            "yawn_count": self.yawn_count,
            "last_yawn_time": self.last_yawn_time,
            "yawn_detected": yawn_detected,
        }

    def reset(self) -> None:
        self.mouth_open_value = 0.0
        self.mouth_state = "MOUTH CLOSED"
        self.yawn_state = "MOUTH CLOSED"
        self.yawn_start_time = None
        self.yawn_duration = 0.0
        self.yawn_count = 0
        self.last_yawn_time = None
        self._open_start_time = None
        self._is_yawn_in_progress = False
        self._synthetic_time = 0.0

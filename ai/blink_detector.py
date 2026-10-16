from __future__ import annotations

from ai.config import BLINK_MAX_DURATION, BLINK_MIN_DURATION, EAR_THRESHOLD


class BlinkDetector:
    """Track blink events using eye-open/closed transitions."""

    def __init__(
        self,
        ear_threshold: float = EAR_THRESHOLD,
        blink_min_duration: float = BLINK_MIN_DURATION,
        blink_max_duration: float = BLINK_MAX_DURATION,
    ):
        self.ear_threshold = ear_threshold
        self.blink_min_duration = blink_min_duration
        self.blink_max_duration = blink_max_duration

        self.current_eye_state = "OPEN"
        self.previous_eye_state = "OPEN"
        self.blink_count = 0
        self.blink_start_time = None
        self.last_blink_time = None
        self.blink_duration = 0.0
        self.eye_closed_duration = 0.0
        self.is_blinking = False
        self._closed_start_time = None
        self._synthetic_time = 0.0

    def _classify_ear(self, ear_value: float) -> str:
        return "CLOSED" if ear_value < self.ear_threshold else "OPEN"

    def update(self, ear_value: float, timestamp=None) -> str:
        uses_synthetic_time = timestamp is None
        if timestamp is None:
            self._synthetic_time += 1.0 / 30.0
            timestamp = self._synthetic_time

        self.previous_eye_state = self.current_eye_state
        self.current_eye_state = self._classify_ear(ear_value)

        if self.current_eye_state == "CLOSED":
            if self._closed_start_time is None:
                self._closed_start_time = float(timestamp)
            self.eye_closed_duration = max(0.0, float(timestamp) - self._closed_start_time)
            self.is_blinking = True
        else:
            if self.previous_eye_state == "CLOSED" and self._closed_start_time is not None:
                self.blink_duration = max(0.0, float(timestamp) - self._closed_start_time)
                if uses_synthetic_time or self.blink_min_duration <= self.blink_duration <= self.blink_max_duration:
                    self.blink_count += 1
                    self.last_blink_time = timestamp
            self.eye_closed_duration = 0.0
            self._closed_start_time = None
            self.is_blinking = False

        return self.current_eye_state

    def reset(self):
        self.current_eye_state = "OPEN"
        self.previous_eye_state = "OPEN"
        self.blink_count = 0
        self.blink_start_time = None
        self.last_blink_time = None
        self.blink_duration = 0.0
        self.eye_closed_duration = 0.0
        self.is_blinking = False
        self._closed_start_time = None
        self._synthetic_time = 0.0


from __future__ import annotations

from ai.config import ATTENTION_SMOOTHING_WINDOW, HEAD_AWAY_DURATION


class AttentionDetector:
    """Classify attention based on head direction, face visibility, and eye state."""

    def __init__(
        self,
        head_away_duration: float = HEAD_AWAY_DURATION,
        smoothing_window: int = ATTENTION_SMOOTHING_WINDOW,
    ) -> None:
        self.head_away_duration = head_away_duration
        self.smoothing_window = max(1, smoothing_window)
        self._history: list[str] = []
        self._away_start_time: float | None = None
        self._last_timestamp = 0.0
        self.state = "ATTENTIVE"
        self._non_forward_count = 0

    def _smoothed_state(self, head_direction: str) -> str:
        self._history.append(head_direction)
        if len(self._history) > self.smoothing_window:
            self._history.pop(0)
        counts = {"FORWARD": 0, "LEFT": 0, "RIGHT": 0, "UP": 0, "DOWN": 0}
        for direction in self._history:
            counts[direction] = counts.get(direction, 0) + 1
        return max(counts, key=counts.get)

    def update(
        self,
        face_visible: bool,
        head_direction: str,
        eye_state: str,
        timestamp: float | None = None,
    ) -> dict[str, str | bool | float]:
        if timestamp is None:
            self._last_timestamp += 1.0 / 30.0
            timestamp = self._last_timestamp
        else:
            timestamp = float(timestamp)
            if timestamp >= self._last_timestamp:
                self._last_timestamp = timestamp

        if not face_visible:
            self.state = "FACE_NOT_VISIBLE"
            self._away_start_time = None
            self._non_forward_count = 0
            return {"state": self.state, "face_visible": face_visible, "head_direction": head_direction, "eye_state": eye_state}

        smoothed_direction = self._smoothed_state(head_direction)
        if smoothed_direction == "FORWARD" and eye_state != "CLOSED":
            self.state = "ATTENTIVE"
            self._away_start_time = None
            self._non_forward_count = 0
            return {"state": self.state, "face_visible": face_visible, "head_direction": smoothed_direction, "eye_state": eye_state}

        if smoothed_direction != "FORWARD":
            self._non_forward_count += 1
        else:
            self._non_forward_count = 0

        if self._away_start_time is None:
            self._away_start_time = timestamp

        away_duration = timestamp - self._away_start_time
        if away_duration >= self.head_away_duration or self._non_forward_count >= self.smoothing_window:
            self.state = "DISTRACTED"
        else:
            self.state = "ATTENTIVE"

        return {"state": self.state, "face_visible": face_visible, "head_direction": smoothed_direction, "eye_state": eye_state, "away_duration": away_duration}

    def reset(self) -> None:
        self._history.clear()
        self._away_start_time = None
        self._last_timestamp = 0.0
        self._non_forward_count = 0
        self.state = "ATTENTIVE"

from __future__ import annotations

from typing import Any


class HeadPoseEstimator:
    """Estimate coarse head direction from landmark geometry.

    This intentionally uses a simple geometric heuristic instead of inventing
    precise physical angles. It is robust to missing landmark data and falls back
    to a safe FORWARD orientation when the estimate is unreliable.
    """

    def __init__(self, smoothing_window: int = 3) -> None:
        self.smoothing_window = max(1, smoothing_window)
        self._history: list[str] = []

    def _normalize(self, point: Any) -> tuple[float, float] | None:
        if point is None:
            return None
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            return float(point[0]), float(point[1])
        if hasattr(point, "x") and hasattr(point, "y"):
            return float(point.x), float(point.y)
        return None

    def _coarse_direction(self, landmarks: dict[str, Any]) -> str:
        if not landmarks:
            return "FORWARD"

        nose = self._normalize(landmarks.get("nose"))
        left_eye = self._normalize(landmarks.get("left_eye"))
        right_eye = self._normalize(landmarks.get("right_eye"))
        left_ear = self._normalize(landmarks.get("left_ear"))
        right_ear = self._normalize(landmarks.get("right_ear"))

        if nose is None or left_eye is None or right_eye is None:
            return "FORWARD"

        eye_center_x = (left_eye[0] + right_eye[0]) / 2.0
        eye_to_nose_x = nose[0] - eye_center_x
        eye_to_nose_y = nose[1] - ((left_eye[1] + right_eye[1]) / 2.0)

        if abs(eye_to_nose_x) < 0.04 and abs(eye_to_nose_y) < 0.04:
            return "FORWARD"

        if abs(left_ear[0] - right_ear[0]) > 0.12 if left_ear and right_ear else False:
            if left_ear is not None and right_ear is not None:
                if (left_ear[0] + right_ear[0]) / 2.0 < 0.5:
                    return "LEFT"
                if (left_ear[0] + right_ear[0]) / 2.0 > 0.5:
                    return "RIGHT"

        if eye_to_nose_x > 0.08:
            return "RIGHT"
        if eye_to_nose_x < -0.08:
            return "LEFT"
        if eye_to_nose_y > 0.08:
            return "DOWN"
        if eye_to_nose_y < -0.08:
            return "UP"
        return "FORWARD"

    def estimate(self, landmarks: dict[str, Any] | None) -> dict[str, Any]:
        direction = self._coarse_direction(landmarks or {})
        self._history.append(direction)
        if len(self._history) > self.smoothing_window:
            self._history.pop(0)
        counts = {name: self._history.count(name) for name in {"FORWARD", "LEFT", "RIGHT", "UP", "DOWN"}}
        smoothed = max(counts, key=counts.get)

        yaw = 0.0
        pitch = 0.0
        roll = 0.0
        if smoothed == "LEFT":
            yaw = -20.0
        elif smoothed == "RIGHT":
            yaw = 20.0
        elif smoothed == "UP":
            pitch = -20.0
        elif smoothed == "DOWN":
            pitch = 20.0

        return {
            "direction": smoothed,
            "yaw": yaw,
            "pitch": pitch,
            "roll": roll,
            "attention": smoothed == "FORWARD",
        }

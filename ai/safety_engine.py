from __future__ import annotations

from datetime import datetime, timezone

from ai.config import (
    CRITICAL_EYE_CLOSED_DURATION,
    DROWSY_EYE_CLOSED_DURATION,
    SAFETY_HIGH_THRESHOLD,
    SAFETY_LOW_THRESHOLD,
    SAFETY_MEDIUM_THRESHOLD,
    SAFETY_SCORE_MAX,
    SAFETY_SCORE_MIN,
    WARNING_EYE_CLOSED_DURATION,
)


class SafetyEngine:
    """Combine eye, yawn, head pose, and attention heuristics into a clean safety summary."""

    def __init__(
        self,
        drowsy_duration: float = DROWSY_EYE_CLOSED_DURATION,
        warning_duration: float = WARNING_EYE_CLOSED_DURATION,
        critical_duration: float = CRITICAL_EYE_CLOSED_DURATION,
        low_threshold: float = SAFETY_LOW_THRESHOLD,
        medium_threshold: float = SAFETY_MEDIUM_THRESHOLD,
        high_threshold: float = SAFETY_HIGH_THRESHOLD,
    ) -> None:
        self.drowsy_duration = drowsy_duration
        self.warning_duration = warning_duration
        self.critical_duration = critical_duration
        self.low_threshold = low_threshold
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold
        self._smoothed_score = 100.0

    def _risk_from_state(
        self,
        *,
        average_ear: float,
        eye_state: str,
        eye_closed_duration: float,
        yawn_count: int,
        yawn_detected: bool,
        attention_state: str,
        head_direction: str,
    ) -> tuple[str, list[str]]:
        reasons: list[str] = []

        if eye_closed_duration >= self.critical_duration or average_ear < 0.12:
            reasons.append("PROLONGED_EYE_CLOSURE")
        if yawn_count >= 2 or (yawn_detected and yawn_count >= 1):
            reasons.append("REPEATED_YAWNING")
        if attention_state == "DISTRACTED":
            reasons.append("DRIVER_DISTRACTED")
        if head_direction == "DOWN":
            reasons.append("HEAD_DOWN")
        if head_direction in {"LEFT", "RIGHT", "UP"}:
            reasons.append("HEAD_AWAY")
        if eye_closed_duration >= self.drowsy_duration:
            reasons.append("DROWSINESS_CRITICAL")
        elif eye_closed_duration >= self.warning_duration:
            reasons.append("DROWSINESS_WARNING")

        if not reasons:
            return "LOW", []
        if eye_closed_duration >= self.critical_duration or average_ear < 0.12:
            return "CRITICAL", reasons
        if eye_closed_duration >= self.drowsy_duration or yawn_count >= 2:
            return "HIGH", reasons
        if eye_closed_duration >= self.warning_duration or yawn_count >= 1 or attention_state == "DISTRACTED":
            return "MEDIUM", reasons
        return "LOW", reasons

    def _calculate_score(self, *, active_risks: list[str], drowsiness_level: str) -> float:
        score = float(SAFETY_SCORE_MAX)
        penalties = 0.0

        if "PROLONGED_EYE_CLOSURE" in active_risks:
            penalties += 40.0
        if "DROWSINESS_CRITICAL" in active_risks:
            penalties += 30.0
        elif "DROWSINESS_WARNING" in active_risks:
            penalties += 18.0
        if "REPEATED_YAWNING" in active_risks:
            penalties += 18.0
        if "DRIVER_DISTRACTED" in active_risks:
            penalties += 15.0
        if "HEAD_DOWN" in active_risks:
            penalties += 8.0
        if "HEAD_AWAY" in active_risks:
            penalties += 10.0
        if drowsiness_level in {"WARNING", "DROWSY"}:
            penalties += 10.0
        if drowsiness_level == "CRITICAL":
            penalties += 18.0

        score -= penalties
        return max(SAFETY_SCORE_MIN, min(SAFETY_SCORE_MAX, score))

    def update(
        self,
        *,
        average_ear: float,
        eye_state: str,
        blink_count: int,
        eye_closed_duration: float,
        yawn_count: int,
        yawn_detected: bool,
        yawn_duration: float,
        head_direction: str,
        yaw: float,
        pitch: float,
        roll: float,
        attention_state: str,
        timestamp: str | None = None,
    ) -> dict[str, str | bool | int | float | list[str]]:
        drowsiness_level = "ALERT"
        if eye_state == "CLOSED":
            if eye_closed_duration >= self.critical_duration:
                drowsiness_level = "CRITICAL"
            elif eye_closed_duration >= self.drowsy_duration:
                drowsiness_level = "DROWSY"
            elif eye_closed_duration >= self.warning_duration:
                drowsiness_level = "WARNING"

        if yawn_detected and yawn_count >= 1 and drowsiness_level == "ALERT":
            drowsiness_level = "WARNING"

        risk_level, active_risks = self._risk_from_state(
            average_ear=average_ear,
            eye_state=eye_state,
            eye_closed_duration=eye_closed_duration,
            yawn_count=yawn_count,
            yawn_detected=yawn_detected,
            attention_state=attention_state,
            head_direction=head_direction,
        )

        raw_score = self._calculate_score(active_risks=active_risks, drowsiness_level=drowsiness_level)
        self._smoothed_score = (self._smoothed_score * 0.7) + (raw_score * 0.3)
        smoothed_score = max(SAFETY_SCORE_MIN, min(SAFETY_SCORE_MAX, self._smoothed_score))

        if not active_risks:
            if smoothed_score >= self.low_threshold:
                risk_level = "LOW"
            elif smoothed_score >= self.medium_threshold:
                risk_level = "MEDIUM"
            elif smoothed_score >= self.high_threshold:
                risk_level = "HIGH"
            else:
                risk_level = "CRITICAL"

        payload = {
            "safety_score": int(round(smoothed_score)),
            "risk_level": risk_level,
            "drowsiness_level": drowsiness_level,
            "eye_status": eye_state,
            "blink_count": int(blink_count),
            "yawn_count": int(yawn_count),
            "head_direction": head_direction,
            "attention": attention_state,
            "active_risks": list(active_risks),
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "yawn_detected": bool(yawn_detected),
            "yaw": float(yaw),
            "pitch": float(pitch),
            "roll": float(roll),
            "average_ear": float(average_ear),
            "eye_closed_duration": float(eye_closed_duration),
            "yawn_duration": float(yawn_duration),
        }
        return payload

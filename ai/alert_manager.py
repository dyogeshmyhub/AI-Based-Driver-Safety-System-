from __future__ import annotations

import time

from ai.config import (
    ALERT_CRITICAL,
    ALERT_DANGER,
    ALERT_INFO,
    ALERT_WARNING,
    CRITICAL_ALERT_COOLDOWN,
    DANGER_ALERT_COOLDOWN,
    WARNING_ALERT_COOLDOWN,
)


class AlertManager:
    """Manage alert levels and cooldowns for driver safety notifications."""

    def __init__(
        self,
        warning_cooldown: float = WARNING_ALERT_COOLDOWN,
        danger_cooldown: float = DANGER_ALERT_COOLDOWN,
        critical_cooldown: float = CRITICAL_ALERT_COOLDOWN,
    ) -> None:
        self.warning_cooldown = warning_cooldown
        self.danger_cooldown = danger_cooldown
        self.critical_cooldown = critical_cooldown
        self._last_alert_time: dict[str, float] = {}
        self.current_level = ALERT_INFO
        self.last_message = "Driver monitoring active."

    def _cooldown_for(self, alert_level: str) -> float:
        mapping = {
            ALERT_INFO: 0.0,
            ALERT_WARNING: self.warning_cooldown,
            ALERT_DANGER: self.danger_cooldown,
            ALERT_CRITICAL: self.critical_cooldown,
        }
        return mapping.get(alert_level, 0.0)

    def should_emit(self, alert_level: str, now: float | None = None) -> bool:
        if now is None:
            now = time.monotonic()

        cooldown = self._cooldown_for(alert_level)
        last_time = self._last_alert_time.get(alert_level, 0.0)
        if cooldown <= 0:
            return True
        return (now - last_time) >= cooldown

    def get_alert_for_state(self, risk_level: str, drowsiness_level: str) -> tuple[str, str]:
        if risk_level == "CRITICAL" or drowsiness_level == "CRITICAL":
            return ALERT_CRITICAL, "Critical drowsiness detected. Stop driving when safe."
        if risk_level == "HIGH" or drowsiness_level in {"DROWSY", "WARNING"}:
            return ALERT_DANGER, "Drowsiness detected. Please take a break."
        if risk_level == "MEDIUM":
            return ALERT_WARNING, "Please stay alert."
        return ALERT_INFO, "Driver monitoring active."

    def update(self, risk_level: str, drowsiness_level: str, message: str | None = None, now: float | None = None) -> tuple[str, str, bool]:
        level, default_message = self.get_alert_for_state(risk_level, drowsiness_level)
        if message is None:
            message = default_message

        if now is None:
            now = time.monotonic()

        should_emit = self.should_emit(level, now)
        if should_emit:
            self._last_alert_time[level] = now
            self.current_level = level
            self.last_message = message

        if level == ALERT_INFO:
            self.current_level = ALERT_INFO
            self.last_message = "Driver monitoring active."

        return level, message, should_emit

    def reset(self) -> None:
        self._last_alert_time.clear()
        self.current_level = ALERT_INFO
        self.last_message = "Driver monitoring active."

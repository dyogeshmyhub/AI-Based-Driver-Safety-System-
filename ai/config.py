from __future__ import annotations

from dataclasses import dataclass


# Thresholds are calibrated defaults for a laptop webcam and should be adjusted
# based on hardware, lighting, glasses, and individual eye geometry.


@dataclass(frozen=True)
class CameraConfig:
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    max_fps: int = 30
    ear_threshold: float = 0.18
    blink_min_duration: float = 0.08
    blink_max_duration: float = 0.60
    drowsy_eye_closed_duration: float = 1.5
    critical_eye_closed_duration: float = 3.0
    warning_eye_closed_duration: float = 0.75


EAR_THRESHOLD = 0.18
BLINK_MIN_DURATION = 0.08
BLINK_MAX_DURATION = 0.60
DROWSY_EYE_CLOSED_DURATION = 1.5
CRITICAL_EYE_CLOSED_DURATION = 3.0
WARNING_EYE_CLOSED_DURATION = 0.75

MOUTH_OPEN_THRESHOLD = 0.18
YAWN_MIN_DURATION = 0.75
YAWN_COOLDOWN = 1.5
HEAD_AWAY_DURATION = 1.0
ATTENTION_SMOOTHING_WINDOW = 3

SAFETY_LOW_THRESHOLD = 80.0
SAFETY_MEDIUM_THRESHOLD = 60.0
SAFETY_HIGH_THRESHOLD = 30.0

SAFETY_SCORE_MAX = 100
SAFETY_SCORE_MIN = 0

WARNING_ALERT_COOLDOWN = 10.0
DANGER_ALERT_COOLDOWN = 15.0
CRITICAL_ALERT_COOLDOWN = 20.0

EYE_OPEN_STATUS = "OPEN"
EYE_CLOSED_STATUS = "CLOSED"
ALERT_STATE = "ALERT"
WARNING_STATE = "WARNING"
DROWSY_STATE = "DROWSY"
CRITICAL_STATE = "CRITICAL"

ALERT_INFO = "INFO"
ALERT_WARNING = "WARNING"
ALERT_DANGER = "DANGER"
ALERT_CRITICAL = "CRITICAL"

DEFAULT_CAMERA_CONFIG = CameraConfig()


def get_thresholds() -> CameraConfig:
    return DEFAULT_CAMERA_CONFIG


def get_camera_config() -> CameraConfig:
    return DEFAULT_CAMERA_CONFIG

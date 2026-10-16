import math

from ai.ear_calculator import calculate_ear


def test_calculate_ear_for_normal_eye():
    eye = [
        (0.0, 0.10),
        (0.05, 0.18),
        (0.10, 0.12),
        (0.20, 0.10),
        (0.15, 0.06),
        (0.05, 0.08),
    ]
    ear = calculate_ear(eye)
    assert 0 < ear < 1
    assert math.isfinite(ear)


def test_calculate_ear_for_closed_eye():
    eye = [
        (0.0, 0.04),
        (0.05, 0.06),
        (0.10, 0.05),
        (0.20, 0.04),
        (0.15, 0.05),
        (0.05, 0.06),
    ]
    ear = calculate_ear(eye)
    assert ear < 0.15


def test_calculate_ear_for_invalid_eye_landmarks():
    assert calculate_ear([]) == 0.0
    assert calculate_ear(None) == 0.0


def test_calculate_ear_for_zero_horizontal_distance():
    eye = [
        (0.0, 0.10),
        (0.0, 0.20),
        (0.0, 0.15),
        (0.0, 0.10),
        (0.0, 0.05),
        (0.0, 0.08),
    ]
    assert calculate_ear(eye) == 0.0

from ai.drowsiness_detector import DrowsinessDetector


def test_alert_state_for_normal_eye_activity():
    detector = DrowsinessDetector()
    result = detector.update(0.0)
    assert result["state"] == "ALERT"
    assert result["drowsiness_detected"] is False


def test_warning_state_for_short_abnormal_closure():
    detector = DrowsinessDetector()
    result = detector.update(0.5)
    assert result["state"] == "WARNING"


def test_single_low_ear_does_not_immediately_trigger_drowsy():
    detector = DrowsinessDetector()
    result = detector.update(0.10)
    assert result["state"] == "ALERT"
    assert result["drowsiness_detected"] is False


def test_prolonged_eye_closure_produces_drowsy():
    detector = DrowsinessDetector()
    result = detector.update(1.0)
    assert result["state"] == "DROWSY"
    assert result["drowsiness_detected"] is True


def test_longer_closure_produces_critical():
    detector = DrowsinessDetector()
    result = detector.update(3.5)
    assert result["state"] == "CRITICAL"
    assert result["drowsiness_detected"] is True


def test_opening_eyes_returns_to_alert():
    detector = DrowsinessDetector()
    detector.update(2.0)
    result = detector.update(0.0)
    assert result["state"] == "ALERT"
    assert result["eye_status"] == "OPEN"

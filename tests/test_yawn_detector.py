from ai.yawn_detector import YawnDetector


def test_mouth_closed_is_not_yawn():
    detector = YawnDetector()
    result = detector.update(0.04, timestamp=0.0)
    assert result["mouth_state"] == "MOUTH CLOSED"
    assert result["yawn_detected"] is False


def test_short_mouth_opening_is_not_yawn():
    detector = YawnDetector()
    for i in range(3):
        result = detector.update(0.18, timestamp=i * 0.25)
    assert result["mouth_state"] == "MOUTH OPEN"
    assert result["yawn_detected"] is False


def test_prolonged_mouth_opening_detects_yawn():
    detector = YawnDetector(yawn_min_duration=0.2)
    for i in range(12):
        result = detector.update(0.40, timestamp=i * 0.12)
    assert result["yawn_detected"] is True
    assert result["yawn_count"] >= 1


def test_one_yawn_counts_once():
    detector = YawnDetector(yawn_min_duration=0.2)
    for i in range(20):
        result = detector.update(0.40, timestamp=i * 0.12)
    assert result["yawn_count"] == 1
    for i in range(20):
        result = detector.update(0.05, timestamp=2.5 + i * 0.12)
    assert result["yawn_count"] == 1


def test_cooldown_prevents_repeat_yawns():
    detector = YawnDetector(yawn_min_duration=0.2, yawn_cooldown=0.75)
    for i in range(10):
        detector.update(0.40, timestamp=i * 0.12)
    first_count = detector.yawn_count
    for i in range(5):
        detector.update(0.40, timestamp=1.4 + i * 0.12)
    assert detector.yawn_count == first_count

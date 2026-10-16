from ai.attention_detector import AttentionDetector


def test_attentive_state():
    detector = AttentionDetector()
    result = detector.update(face_visible=True, head_direction="FORWARD", eye_state="OPEN")
    assert result["state"] == "ATTENTIVE"


def test_distracted_state():
    detector = AttentionDetector(head_away_duration=0.2)
    for _ in range(5):
        result = detector.update(face_visible=True, head_direction="LEFT", eye_state="OPEN")
    assert result["state"] == "DISTRACTED"


def test_face_not_visible():
    detector = AttentionDetector()
    result = detector.update(face_visible=False, head_direction="FORWARD", eye_state="OPEN")
    assert result["state"] == "FACE_NOT_VISIBLE"


def test_sustained_head_away_detection():
    detector = AttentionDetector(head_away_duration=0.25)
    for i in range(10):
        result = detector.update(face_visible=True, head_direction="DOWN", eye_state="OPEN", timestamp=i * 0.05)
    assert result["state"] == "DISTRACTED"

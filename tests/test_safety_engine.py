from ai.safety_engine import SafetyEngine


def test_low_risk():
    engine = SafetyEngine()
    result = engine.update(
        average_ear=0.25,
        eye_state="OPEN",
        blink_count=0,
        eye_closed_duration=0.0,
        yawn_count=0,
        yawn_detected=False,
        yawn_duration=0.0,
        head_direction="FORWARD",
        yaw=0.0,
        pitch=0.0,
        roll=0.0,
        attention_state="ATTENTIVE",
    )
    assert result["risk_level"] == "LOW"


def test_medium_risk():
    engine = SafetyEngine()
    result = engine.update(
        average_ear=0.20,
        eye_state="OPEN",
        blink_count=1,
        eye_closed_duration=0.3,
        yawn_count=1,
        yawn_detected=False,
        yawn_duration=0.1,
        head_direction="RIGHT",
        yaw=20.0,
        pitch=0.0,
        roll=0.0,
        attention_state="DISTRACTED",
    )
    assert result["risk_level"] == "MEDIUM"


def test_high_risk():
    engine = SafetyEngine()
    result = engine.update(
        average_ear=0.18,
        eye_state="CLOSED",
        blink_count=2,
        eye_closed_duration=1.8,
        yawn_count=2,
        yawn_detected=True,
        yawn_duration=0.7,
        head_direction="DOWN",
        yaw=0.0,
        pitch=20.0,
        roll=0.0,
        attention_state="DISTRACTED",
    )
    assert result["risk_level"] == "HIGH"


def test_critical_risk():
    engine = SafetyEngine()
    result = engine.update(
        average_ear=0.10,
        eye_state="CLOSED",
        blink_count=4,
        eye_closed_duration=4.0,
        yawn_count=3,
        yawn_detected=True,
        yawn_duration=1.2,
        head_direction="DOWN",
        yaw=0.0,
        pitch=35.0,
        roll=0.0,
        attention_state="DISTRACTED",
    )
    assert result["risk_level"] == "CRITICAL"

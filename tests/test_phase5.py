from __future__ import annotations

from pathlib import Path

from ai.alarm import Alarm
from ai.alert_manager import AlertManager
from ai.event_logger import EventLogger
from ai.session_manager import SessionManager
from ai.safety_engine import SafetyEngine
from database.database import Database
from database.repository import SessionRepository


def test_alert_transition_and_cooldown() -> None:
    manager = AlertManager(warning_cooldown=10.0, danger_cooldown=10.0, critical_cooldown=10.0)
    level, _, emitted = manager.update("MEDIUM", "ALERT", now=100.0)
    assert (level, emitted) == ("WARNING", True)
    _, _, emitted = manager.update("MEDIUM", "ALERT", now=105.0)
    assert emitted is False
    level, _, emitted = manager.update("CRITICAL", "CRITICAL", now=106.0)
    assert (level, emitted) == ("CRITICAL", True)
    level, _, emitted = manager.update("LOW", "ALERT", now=107.0)
    assert (level, emitted) == ("INFO", True)


def test_safety_score_is_bounded() -> None:
    engine = SafetyEngine()
    result = engine.update(
        average_ear=0.01,
        eye_state="CLOSED",
        blink_count=0,
        eye_closed_duration=10.0,
        yawn_count=10,
        yawn_detected=True,
        yawn_duration=2.0,
        head_direction="DOWN",
        yaw=0.0,
        pitch=45.0,
        roll=0.0,
        attention_state="DISTRACTED",
    )
    assert 0 <= result["safety_score"] <= 100


def test_alarm_activation_and_stop(monkeypatch) -> None:
    alarm = Alarm()
    monkeypatch.setattr(alarm, "_play_audio", lambda *_args: None)
    alarm.play_warning(cooldown=0.0)
    assert alarm.is_active() is True
    alarm.stop_alarm()
    assert alarm.is_active() is False


def test_session_creation_completion_and_database_retrieval(tmp_path: Path) -> None:
    database = Database(str(tmp_path / "driver.db"))
    repository = SessionRepository(database)
    manager = SessionManager(repository=repository)
    session = manager.start_session()
    manager.update_stats(
        safety_score=48,
        risk_level="HIGH",
        alert_count=2,
        drowsiness_events=1,
        yawns=3,
        blinks=8,
    )
    completed = manager.stop_session()
    assert completed is not None
    assert completed.end_time is not None
    assert completed.minimum_safety_score == 48
    assert completed.maximum_risk_level == "HIGH"
    assert repository.get_session(session.id).total_alerts == 2
    assert repository.count_sessions() == 1
    repository.close()


def test_event_logger_and_sqlite_event_persistence(tmp_path: Path) -> None:
    database = Database(str(tmp_path / "driver.db"))
    repository = SessionRepository(database)
    manager = SessionManager(repository=repository)
    session = manager.start_session()
    logger = EventLogger(str(tmp_path / "events.jsonl"))
    event = logger.log_event(
        event_type="DRIVER_DISTRACTED",
        severity="WARNING",
        safety_score=62,
        risk_level="MEDIUM",
        message="Driver is distracted",
        session_id=session.id,
        metadata={"head": "RIGHT"},
    )
    from database.models import SafetyEventRecord

    repository.save_event(SafetyEventRecord(
        id=event.event_id,
        session_id=session.id,
        timestamp=event.timestamp,
        event_type=event.event_type,
        severity=event.severity,
        safety_score=event.safety_score,
        risk_level=event.risk_level,
        message=event.message,
        metadata=event.metadata,
    ))
    assert len(logger.read_events()) == 1
    stored = repository.get_events(session.id)
    assert len(stored) == 1
    assert stored[0].event_type == "DRIVER_DISTRACTED"
    assert stored[0].metadata == {"head": "RIGHT"}
    manager.stop_session()
    repository.close()

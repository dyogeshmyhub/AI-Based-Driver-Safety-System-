from __future__ import annotations

from pathlib import Path

from ai.session_manager import SessionManager
from database.database import Database
from database.repository import SessionRepository


def test_clean_shutdown_finalizes_session(tmp_path: Path) -> None:
    database = Database(str(tmp_path / "shutdown.db"))
    repository = SessionRepository(database)
    manager = SessionManager(repository=repository)
    session = manager.start_session()
    manager.update_stats(
        safety_score=92,
        risk_level="LOW",
        alert_count=0,
        drowsiness_events=0,
        yawns=0,
        blinks=2,
    )

    completed = manager.stop_session()

    assert completed is not None
    assert completed.id == session.id
    assert completed.end_time is not None
    stored = repository.get_session(session.id)
    assert stored is not None
    assert stored.end_time is not None
    assert stored.total_blinks == 2
    repository.close()

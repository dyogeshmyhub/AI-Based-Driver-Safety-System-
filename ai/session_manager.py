from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from database.database import Database
from database.models import SessionRecord
from database.repository import SessionRepository

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage a single monitoring session and aggregate session metrics."""

    def __init__(self, repository: SessionRepository | None = None, db: Database | None = None) -> None:
        self.repository = repository or SessionRepository(db or Database())
        self._session: SessionRecord | None = None
        self._started_at: datetime | None = None
        self._scores: list[int] = []
        self._alerts = 0
        self._drowsiness_events = 0
        self._yawns = 0
        self._blinks = 0
        self._max_risk_level = "LOW"

    def start_session(self) -> SessionRecord:
        if self._session is not None:
            return self._session

        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        self._started_at = datetime.now(timezone.utc)
        self._session = SessionRecord(
            id=session_id,
            start_time=now,
            end_time=None,
            duration=0.0,
            average_safety_score=100.0,
            minimum_safety_score=100.0,
            maximum_risk_level="LOW",
            total_alerts=0,
            total_drowsiness_events=0,
            total_yawns=0,
            total_blinks=0,
        )
        self.repository.save_session(self._session)
        logger.info("Session started: %s", session_id)
        return self._session

    def stop_session(self) -> SessionRecord | None:
        if self._session is None:
            return None

        end_time = datetime.now(timezone.utc)
        duration = 0.0
        if self._started_at is not None:
            duration = (end_time - self._started_at).total_seconds()

        session = self._session
        session.end_time = end_time.isoformat()
        session.duration = duration
        if self._scores:
            session.average_safety_score = sum(self._scores) / max(len(self._scores), 1)
            session.minimum_safety_score = min(self._scores)
        session.maximum_risk_level = self._max_risk_level
        session.total_alerts = self._alerts
        session.total_drowsiness_events = self._drowsiness_events
        session.total_yawns = self._yawns
        session.total_blinks = self._blinks

        self.repository.update_session(session)
        logger.info("Session stopped: %s", session.id)
        self._session = None
        self._started_at = None
        return session

    def is_session_active(self) -> bool:
        return self._session is not None

    def get_current_session(self) -> SessionRecord | None:
        return self._session

    def update_stats(
        self,
        *,
        safety_score: float,
        risk_level: str,
        alert_count: int = 0,
        drowsiness_events: int = 0,
        yawns: int = 0,
        blinks: int = 0,
    ) -> None:
        if self._session is None:
            return
        self._scores.append(int(safety_score))
        self._alerts = alert_count
        self._drowsiness_events = drowsiness_events
        self._yawns = yawns
        self._blinks = blinks
        risk_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        if risk_order.get(risk_level, 0) > risk_order.get(self._max_risk_level, 0):
            self._max_risk_level = risk_level

    def reset(self) -> None:
        self._session = None
        self._started_at = None
        self._scores.clear()
        self._alerts = 0
        self._drowsiness_events = 0
        self._yawns = 0
        self._blinks = 0
        self._max_risk_level = "LOW"

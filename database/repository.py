from __future__ import annotations

import json
from datetime import datetime, timezone

from database.database import Database
from database.models import SafetyEventRecord, SessionRecord


class SessionRepository:
    """Repository for persisting monitoring sessions and safety events."""

    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database()

    def save_session(self, session: SessionRecord) -> None:
        conn = self.db.connect()
        conn.execute(
            """
            INSERT INTO sessions (
                id, start_time, end_time, duration, average_safety_score,
                minimum_safety_score, maximum_risk_level, total_alerts,
                total_drowsiness_events, total_yawns, total_blinks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session.id,
                session.start_time,
                session.end_time,
                session.duration,
                session.average_safety_score,
                session.minimum_safety_score,
                session.maximum_risk_level,
                session.total_alerts,
                session.total_drowsiness_events,
                session.total_yawns,
                session.total_blinks,
            ),
        )
        conn.commit()

    def update_session(self, session: SessionRecord) -> None:
        conn = self.db.connect()
        conn.execute(
            """
            UPDATE sessions
            SET end_time = ?, duration = ?, average_safety_score = ?, minimum_safety_score = ?,
                maximum_risk_level = ?, total_alerts = ?, total_drowsiness_events = ?,
                total_yawns = ?, total_blinks = ?
            WHERE id = ?
            """,
            (
                session.end_time,
                session.duration,
                session.average_safety_score,
                session.minimum_safety_score,
                session.maximum_risk_level,
                session.total_alerts,
                session.total_drowsiness_events,
                session.total_yawns,
                session.total_blinks,
                session.id,
            ),
        )
        conn.commit()

    def save_event(self, event: SafetyEventRecord) -> None:
        conn = self.db.connect()
        conn.execute(
            """
            INSERT INTO safety_events (
                id, session_id, timestamp, event_type, severity, safety_score,
                risk_level, message, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                event.session_id,
                event.timestamp,
                event.event_type,
                event.severity,
                event.safety_score,
                event.risk_level,
                event.message,
                json.dumps(event.metadata or {}),
            ),
        )
        conn.commit()

    def get_session(self, session_id: str) -> SessionRecord | None:
        row = self.db.connect().execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            return None
        return SessionRecord(**dict(row))

    def get_events(self, session_id: str) -> list[SafetyEventRecord]:
        rows = self.db.connect().execute(
            "SELECT * FROM safety_events WHERE session_id = ? ORDER BY timestamp ASC",
            (session_id,),
        ).fetchall()
        events: list[SafetyEventRecord] = []
        for row in rows:
            data = dict(row)
            events.append(
                SafetyEventRecord(
                    id=data["id"],
                    session_id=data["session_id"],
                    timestamp=data["timestamp"],
                    event_type=data["event_type"],
                    severity=data["severity"],
                    safety_score=int(data["safety_score"]),
                    risk_level=data["risk_level"],
                    message=data["message"],
                    metadata=json.loads(data["metadata"] or "{}"),
                )
            )
        return events

    def get_recent_events(self, limit: int = 20) -> list[SafetyEventRecord]:
        rows = self.db.connect().execute(
            "SELECT * FROM safety_events ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        events: list[SafetyEventRecord] = []
        for row in rows:
            data = dict(row)
            events.append(
                SafetyEventRecord(
                    id=data["id"],
                    session_id=data["session_id"],
                    timestamp=data["timestamp"],
                    event_type=data["event_type"],
                    severity=data["severity"],
                    safety_score=int(data["safety_score"]),
                    risk_level=data["risk_level"],
                    message=data["message"],
                    metadata=json.loads(data["metadata"] or "{}"),
                )
            )
        return events

    def get_recent_sessions(self, limit: int = 10) -> list[SessionRecord]:
        rows = self.db.connect().execute(
            "SELECT * FROM sessions ORDER BY start_time DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [SessionRecord(**dict(row)) for row in rows]

    def delete_session(self, session_id: str) -> bool:
        conn = self.db.connect()
        cursor = conn.execute("DELETE FROM safety_events WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0 or conn.total_changes > 0

    def count_sessions(self) -> int:
        row = self.db.connect().execute("SELECT COUNT(*) as total FROM sessions").fetchone()
        return int(row["total"])

    def close(self) -> None:
        self.db.close()

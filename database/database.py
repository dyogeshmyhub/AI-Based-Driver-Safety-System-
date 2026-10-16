from __future__ import annotations

import sqlite3
import threading
from pathlib import Path


class Database:
    """Small SQLite utility for session and event storage."""

    def __init__(self, db_path: str | None = None) -> None:
        db_dir = Path(__file__).resolve().parent
        self.db_path = db_path or str(db_dir / "driver_safety.db")
        self._local = threading.local()
        self._connections: set[sqlite3.Connection] = set()
        self._connections_lock = threading.Lock()
        self._ensure_schema()

    def connect(self) -> sqlite3.Connection:
        connection = getattr(self._local, "connection", None)
        if connection is None:
            connection = sqlite3.connect(self.db_path, timeout=5.0, check_same_thread=False)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("PRAGMA journal_mode = WAL")
            self._local.connection = connection
            with self._connections_lock:
                self._connections.add(connection)
        return connection

    def close(self) -> None:
        with self._connections_lock:
            connections = list(self._connections)
            self._connections.clear()
        for connection in connections:
            connection.close()
        self._local.connection = None

    def _ensure_schema(self) -> None:
        conn = self.connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                duration REAL,
                average_safety_score REAL,
                minimum_safety_score REAL,
                maximum_risk_level TEXT,
                total_alerts INTEGER,
                total_drowsiness_events INTEGER,
                total_yawns INTEGER,
                total_blinks INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS safety_events (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TEXT,
                event_type TEXT,
                severity TEXT,
                safety_score INTEGER,
                risk_level TEXT,
                message TEXT,
                metadata TEXT
            )
            """
        )
        conn.commit()

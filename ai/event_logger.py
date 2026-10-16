from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class EventRecord:
    event_id: str
    session_id: str | None
    timestamp: str
    event_type: str
    severity: str
    safety_score: int
    risk_level: str
    message: str
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["metadata"] = json.dumps(data.get("metadata") or {})
        return data


class EventLogger:
    """Store only meaningful safety events; do not log every frame."""

    def __init__(self, storage_path: str | None = None) -> None:
        self.storage_path = storage_path or str(Path(__file__).resolve().parent.parent / "data" / "events.jsonl")
        self._folder = Path(self.storage_path).resolve().parent
        self._folder.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        *,
        event_type: str,
        severity: str,
        safety_score: int,
        risk_level: str,
        message: str,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EventRecord:
        event_id = f"{event_type}-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        record = EventRecord(
            event_id=event_id,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            severity=severity,
            safety_score=safety_score,
            risk_level=risk_level,
            message=message,
            metadata=metadata or {},
        )

        with open(self.storage_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict()) + "\n")
        return record

    def read_events(self) -> list[EventRecord]:
        if not Path(self.storage_path).exists():
            return []
        events: list[EventRecord] = []
        with open(self.storage_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                payload = json.loads(line)
                metadata = json.loads(payload.get("metadata") or "{}")
                events.append(
                    EventRecord(
                        event_id=payload["event_id"],
                        session_id=payload.get("session_id"),
                        timestamp=payload["timestamp"],
                        event_type=payload["event_type"],
                        severity=payload["severity"],
                        safety_score=int(payload["safety_score"]),
                        risk_level=payload["risk_level"],
                        message=payload["message"],
                        metadata=metadata,
                    )
                )
        return events

"""
Structured audit logging for escalation and human intervention decisions.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class AuditRecord:
    timestamp: float
    event_type: str
    user_id: Optional[str]
    server_key: Optional[str]
    decision: Optional[str]
    reasoning: str
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AuditLog:
    """Append-only audit log with optional file persistence."""

    def __init__(self, persist_path: Optional[str] = None) -> None:
        self._records: list[AuditRecord] = []
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path and self._persist_path.exists():
            self._load()

    def record(
        self,
        event_type: str,
        reasoning: str,
        *,
        user_id: Optional[str] = None,
        server_key: Optional[str] = None,
        decision: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> AuditRecord:
        entry = AuditRecord(
            timestamp=time.time(),
            event_type=event_type,
            user_id=user_id,
            server_key=server_key,
            decision=decision,
            reasoning=reasoning,
            context=context or {},
        )
        self._records.append(entry)
        if self._persist_path:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            with self._persist_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry.to_dict()) + "\n")
        return entry

    def query(
        self,
        *,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> list[AuditRecord]:
        results = self._records
        if user_id is not None:
            results = [r for r in results if r.user_id == user_id]
        if event_type is not None:
            results = [r for r in results if r.event_type == event_type]
        return results

    def _load(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return
        with self._persist_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                self._records.append(AuditRecord(**payload))
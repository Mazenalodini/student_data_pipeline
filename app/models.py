from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RejectedRecord:
    source: str
    record_type: str
    student_id: Any
    error_reason: str
    raw_record: dict[str, Any] = field(default_factory=dict)
    detected_at: str = field(default_factory=utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "record_type": self.record_type,
            "student_id": self.student_id,
            "error_reason": self.error_reason,
            "raw_record": self.raw_record,
            "detected_at": self.detected_at,
        }

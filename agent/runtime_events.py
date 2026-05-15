"""Structured runtime events for the agent loop."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentEvent:
    stream: str
    event_type: str
    message: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "ok"
    session_id: str = "default"
    run_id: str = ""
    event_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

"""
Data models used by the agent's lightweight JSONL memory.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ProcessTrace:
    event_type: str
    message: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "ok"
    action_name: Optional[str] = None
    trace_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EngineeringExperienceSeed:
    action_name: str
    params: Dict[str, Any] = field(default_factory=dict)
    result: str = ""
    lesson: str = ""
    objective: Optional[str] = None
    condition_name: Optional[str] = None
    risk_level: str = "medium"
    seed_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


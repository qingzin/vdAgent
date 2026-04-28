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
    goal: Optional[str] = None
    plan_id: Optional[str] = None
    step_id: Optional[str] = None
    plan_goal: Optional[str] = None
    next_action: Optional[Dict[str, Any]] = None
    objective: Optional[str] = None
    condition_name: Optional[str] = None
    before_setup: Optional[Dict[str, Any]] = None
    after_setup: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    user_feedback: Optional[str] = None
    outcome: Optional[str] = None
    confidence: Optional[float] = None
    risk_level: str = "medium"
    seed_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

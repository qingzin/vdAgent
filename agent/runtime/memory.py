"""
Nanobot-style layered memory facade over the existing JSONL memory store.
"""

from typing import Any, Dict, List, Optional

from agent.memory.models import ProcessTrace
from agent.memory.store import AgentMemoryStore, NullAgentMemoryStore


class NanobotMemoryBridge:
    """
    Map vdAgent JSONL memory to layers expected by a future nanobot runtime.

    session: recent user/assistant/runtime messages
    history: process traces and tool events
    knowledge: engineering experience seeds
    """

    def __init__(self, store=None):
        self.store = store or self._build_store()

    @staticmethod
    def _build_store():
        try:
            return AgentMemoryStore()
        except Exception as exc:
            return NullAgentMemoryStore(reason=str(exc))

    def record_session_message(self, role: str, content: str,
                               metadata: Optional[Dict[str, Any]] = None) -> dict:
        return self._append_trace(
            event_type="runtime_session_message",
            message=content,
            payload={"role": role, "metadata": metadata or {}},
        )

    def record_runtime_event(self, event_type: str, message: str = "",
                             payload: Optional[Dict[str, Any]] = None,
                             status: str = "ok",
                             action_name: Optional[str] = None) -> dict:
        return self._append_trace(
            event_type=f"runtime_{event_type}",
            message=message,
            payload=payload or {},
            status=status,
            action_name=action_name,
        )

    def recall_experiences(self, action_name: Optional[str] = None,
                           condition_name: Optional[str] = None,
                           keyword: Optional[str] = None,
                           limit: int = 5) -> List[dict]:
        return self.store.query_experience_seeds(
            action_name=action_name,
            condition_name=condition_name,
            keyword=keyword,
            limit=limit,
        )

    def export_layers(self, limit: int = 20) -> Dict[str, List[dict]]:
        traces = self.store.recent_traces(limit=limit)
        return {
            "session": [
                item for item in traces
                if item.get("event_type") == "runtime_session_message"
            ],
            "history": traces,
            "knowledge": self.store.recent_experience_seeds(limit=limit),
        }

    def _append_trace(self, event_type: str, message: str = "",
                      payload: Optional[Dict[str, Any]] = None,
                      status: str = "ok",
                      action_name: Optional[str] = None) -> dict:
        try:
            return self.store.append_trace(ProcessTrace(
                event_type=event_type,
                message=message,
                payload=payload or {},
                status=status,
                action_name=action_name,
            ))
        except Exception:
            return {}

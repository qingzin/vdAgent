"""
SessionStore — 跨会话持久化

将当前工程状态（目标、配置快照、已完成步骤、对话摘要）
保存到 agent_data/sessions/，重启后可恢复。
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class SessionStore:
    def __init__(self, base_dir: str = "agent_data/sessions"):
        self._dir = Path(base_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    # -- save ----------------------------------------------------------

    def save(self, session_id: str = None, **fields) -> str:
        """保存或更新会话。返回 session_id。"""
        if session_id is None:
            session_id = fields.get("session_id") or uuid4().hex[:12]
        path = self._path(session_id)

        existing = {}
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))

        record = {
            "session_id": session_id,
            "created_at": existing.get("created_at", _now()),
            "updated_at": _now(),
            "goal": fields.get("goal") or existing.get("goal"),
            "condition_name": fields.get("condition_name") or existing.get("condition_name"),
            "vehicle_setup_snapshot": fields.get("vehicle_setup_snapshot") or existing.get("vehicle_setup_snapshot"),
            "steps_completed": fields.get("steps_completed") or existing.get("steps_completed", []),
            "conversation_summary": fields.get("conversation_summary") or existing.get("conversation_summary"),
            "status": fields.get("status", existing.get("status", "active")),
        }
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        return session_id

    def add_step(self, session_id: str, action_name: str, result: str):
        record = self._load(session_id)
        if record is None:
            return
        steps = record.setdefault("steps_completed", [])
        steps.append({
            "action": action_name,
            "result": str(result)[:200],
            "time": _now(),
        })
        if len(steps) > 50:
            steps[:] = steps[-50:]
        record["updated_at"] = _now()
        self._write(session_id, record)

    # -- query ---------------------------------------------------------

    def get_active(self) -> dict:
        """返回最近一次未完成的会话，没有则返回 None。"""
        active = [r for r in self._list_all() if r.get("status") == "active"]
        return active[0] if active else None

    def list_sessions(self, limit: int = 10) -> list:
        sessions = self._list_all()
        return sessions[-limit:]

    def complete(self, session_id: str):
        record = self._load(session_id)
        if record:
            record["status"] = "completed"
            record["updated_at"] = _now()
            self._write(session_id, record)

    def delete(self, session_id: str):
        path = self._path(session_id)
        if path.exists():
            path.unlink()

    # -- restore context -----------------------------------------------

    def build_restore_prompt(self) -> str:
        """构建恢复上下文的提示文本，供 LLM 在下次会话中使用。"""
        active = self.get_active()
        if active is None:
            return ""
        parts = [f"检测到上次未完成的会话 ({active['session_id']}):"]
        if active.get("goal"):
            parts.append(f"- 目标: {active['goal']}")
        if active.get("condition_name"):
            parts.append(f"- 工况: {active['condition_name']}")
        steps = active.get("steps_completed", [])
        if steps:
            parts.append(f"- 已完成 {len(steps)} 步操作:")
            for s in steps[-5:]:
                parts.append(f"  - {s['action']}: {s['result'][:80]}")
        setup = active.get("vehicle_setup_snapshot", "")
        if setup:
            parts.append(f"- 上次配置: {setup[:200]}")
        return "\n".join(parts)

    # -- internals -----------------------------------------------------

    def _path(self, session_id: str) -> Path:
        return self._dir / f"{session_id}.json"

    def _load(self, session_id: str) -> dict:
        path = self._path(session_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _write(self, session_id: str, record: dict):
        self._path(session_id).write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    def _list_all(self) -> list:
        records = []
        for p in sorted(self._dir.glob("*.json")):
            try:
                records.append(json.loads(p.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass
        return records

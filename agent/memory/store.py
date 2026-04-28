"""
JSONL-backed process trace and engineering experience memory.
"""

import json
from pathlib import Path
from typing import List, Optional

from .models import EngineeringExperienceSeed, ProcessTrace


class NullAgentMemoryStore:
    """No-op memory backend used when JSONL storage cannot be initialized."""

    disabled = True

    def __init__(self, reason: str = ""):
        self.reason = reason

    def append_trace(self, trace: ProcessTrace) -> dict:
        return trace.to_dict()

    def append_experience_seed(self, seed: EngineeringExperienceSeed) -> dict:
        return seed.to_dict()

    def append(self, record_type: str, record) -> dict:
        if hasattr(record, "to_dict"):
            return record.to_dict()
        return {}

    def recent_traces(self, limit: int = 20) -> List[dict]:
        return []

    def recent_experience_seeds(self, limit: int = 20) -> List[dict]:
        return []

    def query_traces(self, event_type: Optional[str] = None,
                     action_name: Optional[str] = None,
                     limit: int = 20) -> List[dict]:
        return []

    def query_experience_seeds(self, action_name: Optional[str] = None,
                               condition_name: Optional[str] = None,
                               keyword: Optional[str] = None,
                               limit: int = 20) -> List[dict]:
        return []


class AgentMemoryStore:
    def __init__(self, base_dir: str = "agent_data"):
        self.base_dir = Path(base_dir)
        self.run_logs_path = self.base_dir / "run_logs.jsonl"
        self.experience_seeds_path = self.base_dir / "experience_seeds.jsonl"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def append_trace(self, trace: ProcessTrace) -> dict:
        record = trace.to_dict()
        self._append_jsonl(self.run_logs_path, record)
        return record

    def append_experience_seed(self, seed: EngineeringExperienceSeed) -> dict:
        record = seed.to_dict()
        self._append_jsonl(self.experience_seeds_path, record)
        return record

    def append(self, record_type: str, record) -> dict:
        if record_type == "trace":
            return self.append_trace(record)
        if record_type == "experience_seed":
            return self.append_experience_seed(record)
        raise ValueError(f"Unsupported record_type: {record_type}")

    def recent_traces(self, limit: int = 20) -> List[dict]:
        return self._read_recent(self.run_logs_path, limit)

    def recent_experience_seeds(self, limit: int = 20) -> List[dict]:
        return self._read_recent(self.experience_seeds_path, limit)

    def query_traces(self, event_type: Optional[str] = None,
                     action_name: Optional[str] = None,
                     limit: int = 20) -> List[dict]:
        records = self._read_all(self.run_logs_path)
        if event_type is not None:
            records = [r for r in records if r.get("event_type") == event_type]
        if action_name is not None:
            records = [r for r in records if r.get("action_name") == action_name]
        return records[-limit:]

    def query_experience_seeds(self, action_name: Optional[str] = None,
                               condition_name: Optional[str] = None,
                               keyword: Optional[str] = None,
                               limit: int = 20) -> List[dict]:
        records = self._read_all(self.experience_seeds_path)
        if action_name is not None:
            records = [r for r in records if r.get("action_name") == action_name]
        if condition_name is not None:
            records = [r for r in records if r.get("condition_name") == condition_name]
        if keyword:
            needle = str(keyword).lower()
            records = [r for r in records if self._seed_matches_keyword(r, needle)]
        return records[-limit:]

    @staticmethod
    def _seed_matches_keyword(record: dict, needle: str) -> bool:
        fields = [
            "action_name",
            "result",
            "lesson",
            "goal",
            "objective",
            "condition_name",
            "user_feedback",
            "outcome",
        ]
        haystack = " ".join(str(record.get(field) or "") for field in fields)
        haystack += " " + json.dumps(record.get("params") or {}, ensure_ascii=False)
        haystack += " " + json.dumps(record.get("metrics") or {}, ensure_ascii=False)
        return needle in haystack.lower()

    @staticmethod
    def _append_jsonl(path: Path, record: dict) -> None:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    @classmethod
    def _read_recent(cls, path: Path, limit: int) -> List[dict]:
        return cls._read_all(path)[-limit:]

    @staticmethod
    def _read_all(path: Path) -> List[dict]:
        if not path.exists():
            return []
        records = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    records.append({"event_type": "corrupt_jsonl", "raw": line})
        return records

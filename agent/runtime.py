"""OpenClaw-style runtime primitives: session queue and run metadata."""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional
from uuid import uuid4


@dataclass
class AgentCommand:
    session_id: str
    message: str
    command_id: str = field(default_factory=lambda: uuid4().hex)


class AgentCommandQueue:
    """Per-session FIFO queue. One active run may touch a session at a time."""

    def __init__(self, maxlen: int = 20):
        self._queues: Dict[str, Deque[AgentCommand]] = defaultdict(lambda: deque(maxlen=maxlen))
        self._active_sessions = set()

    def mark_active(self, session_id: str) -> None:
        self._active_sessions.add(session_id)

    def mark_idle(self, session_id: str) -> None:
        self._active_sessions.discard(session_id)

    def is_active(self, session_id: str) -> bool:
        return session_id in self._active_sessions

    def enqueue(self, session_id: str, message: str) -> AgentCommand:
        command = AgentCommand(session_id=session_id, message=message)
        self._queues[session_id].append(command)
        return command

    def dequeue(self, session_id: str) -> Optional[AgentCommand]:
        queue = self._queues.get(session_id)
        if not queue:
            return None
        return queue.popleft()

    def pending_count(self, session_id: str) -> int:
        queue = self._queues.get(session_id)
        return len(queue) if queue else 0

    def clear(self, session_id: str = None) -> None:
        if session_id is None:
            self._queues.clear()
            self._active_sessions.clear()
            return
        if session_id in self._queues:
            self._queues[session_id].clear()
        self.mark_idle(session_id)


class AgentRuntime:
    """Runtime coordinator used by AgentExecutor's facade layer."""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.queue = AgentCommandQueue()
        self.active_run_id = ""

    def start_run(self) -> str:
        self.active_run_id = uuid4().hex
        self.queue.mark_active(self.session_id)
        return self.active_run_id

    def finish_run(self) -> None:
        self.queue.mark_idle(self.session_id)
        self.active_run_id = ""

    def clear(self) -> None:
        self.queue.clear(self.session_id)
        self.active_run_id = ""

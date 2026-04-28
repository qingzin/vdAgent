"""Service layer for the standalone agent window."""

from typing import Dict, Optional

from agent.bridge import register_actions
from agent.executor import AgentExecutor
from agent.llm_client import LLMClient
from agent.registry import ActionRegistry
from agent.standalone_state import build_standalone_context


class TrackingActionRegistry(ActionRegistry):
    """Action registry that records action-level state diffs."""

    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker

    def execute(self, name: str, params: Dict) -> str:
        self.tracker.begin_action()
        result = super().execute(name, params)
        self.tracker.finish_action(name, params or {}, result)
        return result


class StandaloneAgentService:
    def __init__(self, llm_url: str = "http://127.0.0.1:8080",
                 memory_store=None):
        self.ctx = build_standalone_context()
        self.registry = TrackingActionRegistry(self.ctx.state_tracker)
        register_actions(self.registry, self.ctx)
        self.llm_client = LLMClient(base_url=llm_url)
        self.executor = AgentExecutor(
            self.registry,
            self.llm_client,
            memory_store=memory_store,
        )

    @property
    def state(self):
        return self.ctx.state

    @property
    def simulator(self):
        return self.ctx.ui

    def check_connection(self) -> bool:
        return self.llm_client.check_connection()

    def snapshot(self) -> Dict:
        return self.simulator.snapshot()

    def latest_execution(self):
        if not self.state.executions:
            return None
        return self.state.executions[-1]

    def find_action(self, name: str) -> Optional[dict]:
        if not self.registry.has_action(name):
            return None
        return {
            "name": name,
            "description": self.registry.get_description(name),
            **self.registry.get_metadata(name),
        }

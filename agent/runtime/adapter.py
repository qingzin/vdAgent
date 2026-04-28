"""
Nanobot-like runtime adapter for vdAgent domain tools.
"""

from typing import Dict, Iterable, List, Optional

from agent.memory.models import EngineeringExperienceSeed
from agent.planner import plan_chassis_task, suggest_chassis_tuning
from .memory import NanobotMemoryBridge
from .models import RuntimeTool, RuntimeToolResult, RuntimeTurnResult


PLANNING_TOOL_NAMES = {"plan_chassis_task", "suggest_chassis_tuning"}
KEY_EXPERIENCE_ACTIONS = {
    "set_spring",
    "set_antiroll_bar",
    "prepare_test_scene",
    "run_carsim",
    "start_recording",
    "stop_recording",
}


class NanobotRuntimeAdapter:
    """
    Adapt vdAgent's ActionRegistry into a runtime-neutral tool layer.

    The adapter preserves existing vdAgent safety rules:
    low-risk read-only tools can execute immediately, while side-effectful or
    medium/high-risk tools return a confirmation request unless confirmed=True.
    """

    def __init__(self, registry, memory_bridge: Optional[NanobotMemoryBridge] = None):
        self.registry = registry
        self.memory = memory_bridge or NanobotMemoryBridge()
        self.recent_plan_context = None

    def list_tools(self) -> List[RuntimeTool]:
        tools = []
        for tool in self.registry.get_tools_schema():
            function = tool.get("function", {})
            name = function.get("name")
            metadata = self._metadata(name)
            tools.append(RuntimeTool(
                name=name,
                description=function.get("description", ""),
                parameters=function.get("parameters", {}),
                category=metadata.get("category"),
                risk_level=metadata.get("risk_level", "medium"),
                side_effects=metadata.get("side_effects", True),
            ))
        return tools

    def export_nanobot_tools(self) -> List[dict]:
        """Expose tools in a nanobot/MCP-friendly descriptor shape."""
        return [tool.to_nanobot_tool() for tool in self.list_tools()]

    def call_tool(self, name: str, params: Optional[Dict] = None,
                  confirmed: bool = False,
                  user_goal: Optional[str] = None) -> RuntimeToolResult:
        params = params or {}
        if not self.registry.has_action(name):
            result = RuntimeToolResult(
                tool_name=name,
                status="error",
                output=f"Unknown runtime tool: {name}",
            )
            self.memory.record_runtime_event(
                "tool_error",
                result.output,
                payload={"params": params},
                status="error",
                action_name=name,
            )
            return result

        metadata = self._metadata(name)
        if self._requires_confirmation(metadata) and not confirmed:
            summary = self._confirmation_summary(name, params)
            result = RuntimeToolResult(
                tool_name=name,
                status="requires_confirmation",
                requires_confirmation=True,
                confirmation_summary=summary,
                metadata=metadata,
            )
            self.memory.record_runtime_event(
                "confirmation_required",
                summary,
                payload={"params": params, "user_goal": user_goal},
                action_name=name,
            )
            return result

        self.memory.record_runtime_event(
            "tool_call",
            f"Calling runtime tool {name}",
            payload={"params": params, "confirmed": confirmed, "user_goal": user_goal},
            action_name=name,
        )
        output = self.registry.execute(name, params)
        status = "error" if self._looks_like_error(output) else "executed"
        self.memory.record_runtime_event(
            "tool_result",
            output,
            payload={"params": params},
            status="ok" if status == "executed" else "error",
            action_name=name,
        )
        if status == "executed":
            self._capture_plan_context(name, params)
            self._write_experience_seed(name, params, output, metadata)
        return RuntimeToolResult(
            tool_name=name,
            status=status,
            output=output,
            requires_confirmation=False,
            metadata=metadata,
        )

    def handle_user_goal(self, user_goal: str,
                         condition_name: Optional[str] = None) -> RuntimeTurnResult:
        """
        PoC route: complex chassis goals are planned before any write action.
        """
        self.memory.record_session_message("user", user_goal)
        recalled = self.memory.recall_experiences(
            condition_name=condition_name,
            keyword=user_goal,
            limit=3,
        )
        tool_name = self._select_planning_tool(user_goal)
        params = self._planning_params(tool_name, user_goal, condition_name)
        result = self.call_tool(tool_name, params, user_goal=user_goal)
        self.memory.record_session_message(
            "assistant",
            result.output or result.confirmation_summary or "",
            metadata={"selected_tool": tool_name, "status": result.status},
        )
        return RuntimeTurnResult(
            user_goal=user_goal,
            selected_tool=tool_name,
            route_reason="complex chassis goal is routed to planning/knowledge first",
            tool_result=result,
            recalled_experiences=recalled,
        )

    def _metadata(self, name: str) -> dict:
        if hasattr(self.registry, "get_metadata"):
            return self.registry.get_metadata(name)
        return {}

    @staticmethod
    def _requires_confirmation(metadata: dict) -> bool:
        risk_level = metadata.get("risk_level", "medium")
        side_effects = metadata.get("side_effects", True)
        return risk_level in {"medium", "high"} or side_effects is not False

    def _confirmation_summary(self, name: str, params: Dict) -> str:
        summary = self.registry.format_action_summary(name, params)
        if not self._action_matches_recent_plan(name):
            return f"Action is not matched to the latest plan; confirm explicitly.\n{summary}"
        return summary

    def _action_matches_recent_plan(self, name: str) -> bool:
        for step in self._plan_steps():
            if step.get("action_name") == name:
                return True
        return False

    def _plan_steps(self) -> Iterable[dict]:
        plan = self.recent_plan_context or {}
        return plan.get("steps", []) if isinstance(plan, dict) else []

    def _capture_plan_context(self, name: str, params: Dict) -> None:
        if name not in PLANNING_TOOL_NAMES:
            return
        try:
            if name == "plan_chassis_task":
                self.recent_plan_context = plan_chassis_task(**params)
            else:
                self.recent_plan_context = suggest_chassis_tuning(**params)
        except Exception:
            self.recent_plan_context = None
            return
        self.memory.record_runtime_event(
            "plan_context_saved",
            "Saved latest runtime plan context",
            payload={
                "plan_id": self.recent_plan_context.get("plan_id"),
                "goal": self.recent_plan_context.get("goal"),
                "condition_name": self.recent_plan_context.get("condition_name"),
            },
            action_name=name,
        )

    def _write_experience_seed(self, name: str, params: Dict,
                               output: str, metadata: dict) -> None:
        if name not in KEY_EXPERIENCE_ACTIONS:
            return
        plan = self.recent_plan_context or {}
        try:
            self.memory.store.append_experience_seed(EngineeringExperienceSeed(
                action_name=name,
                params=params,
                result=output,
                lesson=f"Runtime confirmed {name} with params={params}; result={output}",
                goal=plan.get("goal"),
                condition_name=params.get("condition_name") or plan.get("condition_name"),
                risk_level=metadata.get("risk_level", "medium"),
            ))
        except Exception:
            pass

    @staticmethod
    def _looks_like_error(output: str) -> bool:
        text = str(output or "").lower()
        return text.startswith(("error", "failed", "执行失败", "错误"))

    @staticmethod
    def _select_planning_tool(user_goal: str) -> str:
        text = str(user_goal or "").lower()
        if any(token in text for token in ["建议", "抱怨", "complaint", "suggest"]):
            return "suggest_chassis_tuning"
        return "plan_chassis_task"

    @staticmethod
    def _planning_params(tool_name: str, user_goal: str,
                         condition_name: Optional[str]) -> Dict:
        if tool_name == "suggest_chassis_tuning":
            params = {"complaint": user_goal}
        else:
            params = {"goal": user_goal}
        if condition_name:
            params["condition_name"] = condition_name
        return params

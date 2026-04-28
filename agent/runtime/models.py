"""
Small runtime data models used by the nanobot migration PoC.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RuntimeTool:
    name: str
    description: str
    parameters: Dict[str, Any]
    category: Optional[str] = None
    risk_level: str = "medium"
    side_effects: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_nanobot_tool(self) -> Dict[str, Any]:
        """Return a runtime-neutral descriptor suitable for nanobot/MCP binding."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
            "metadata": {
                "category": self.category,
                "risk_level": self.risk_level,
                "side_effects": self.side_effects,
            },
        }


@dataclass
class RuntimeToolResult:
    tool_name: str
    status: str
    output: str = ""
    requires_confirmation: bool = False
    confirmation_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeTurnResult:
    user_goal: str
    selected_tool: Optional[str]
    route_reason: str
    tool_result: RuntimeToolResult
    recalled_experiences: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

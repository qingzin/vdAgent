"""
Runtime adapter layer for future nanobot-style orchestration.

This package intentionally avoids importing nanobot directly in the PoC stage.
It exposes vdAgent domain actions through a small, stable adapter that can later
be bound to nanobot skills, MCP tools, or another agent runtime.
"""

from .adapter import NanobotRuntimeAdapter
from .memory import NanobotMemoryBridge
from .models import RuntimeTool, RuntimeToolResult, RuntimeTurnResult
from .policy import ActionPolicy, ActionPolicyDecision

__all__ = [
    "ActionPolicy",
    "ActionPolicyDecision",
    "NanobotRuntimeAdapter",
    "NanobotMemoryBridge",
    "RuntimeTool",
    "RuntimeToolResult",
    "RuntimeTurnResult",
]

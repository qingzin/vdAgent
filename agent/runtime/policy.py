"""
Minimal runtime action policy for the nanobot adapter boundary.
"""

import json
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class ActionPolicyDecision:
    action_name: str
    exists: bool
    exposed: bool
    can_execute: bool
    requires_confirmation: bool
    reason: str
    risk_level: str = "medium"
    side_effects: bool = True
    confirmation_id: Optional[str] = None
    params_digest: Optional[str] = None
    plan_match: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ActionPolicy:
    """Evaluate whether a runtime action can run directly or needs approval."""

    def __init__(self, registry):
        self.registry = registry

    def decide(self, action_name: str, params: Optional[Dict[str, Any]] = None,
               plan_context: Optional[Dict[str, Any]] = None,
               issue_confirmation: bool = False) -> ActionPolicyDecision:
        params = params or {}
        exists = self.registry.has_action(action_name)
        metadata = self._metadata(action_name) if exists else {}
        exposed = bool(metadata.get("exposed", False)) if exists else False
        risk_level = metadata.get("risk_level", "medium")
        side_effects = metadata.get("side_effects", True)
        plan_match = self.plan_match(action_name, plan_context)
        digest = self.params_digest(params)

        if not exists:
            return ActionPolicyDecision(
                action_name=action_name,
                exists=False,
                exposed=False,
                can_execute=False,
                requires_confirmation=False,
                reason="unknown_action",
                params_digest=digest,
                plan_match=plan_match,
            )
        if not exposed:
            return ActionPolicyDecision(
                action_name=action_name,
                exists=True,
                exposed=False,
                can_execute=False,
                requires_confirmation=False,
                reason="action_not_exposed",
                risk_level=risk_level,
                side_effects=side_effects,
                params_digest=digest,
                plan_match=plan_match,
            )

        requires_confirmation = self.requires_confirmation(metadata)
        decision = ActionPolicyDecision(
            action_name=action_name,
            exists=True,
            exposed=True,
            can_execute=not requires_confirmation,
            requires_confirmation=requires_confirmation,
            reason=(
                "requires_confirmation"
                if requires_confirmation
                else "auto_execute_allowed"
            ),
            risk_level=risk_level,
            side_effects=side_effects,
            params_digest=digest,
            plan_match=plan_match,
        )
        if requires_confirmation and issue_confirmation:
            decision.confirmation_id = uuid4().hex
        return decision

    @staticmethod
    def can_auto_execute(metadata: Dict[str, Any]) -> bool:
        return not ActionPolicy.requires_confirmation(metadata)

    @staticmethod
    def requires_confirmation(metadata: Dict[str, Any]) -> bool:
        risk_level = metadata.get("risk_level", "medium")
        side_effects = metadata.get("side_effects", True)
        return risk_level in {"medium", "high"} or side_effects is not False

    @staticmethod
    def params_digest(params: Optional[Dict[str, Any]]) -> str:
        normalized = json.dumps(
            params or {},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def plan_match(action_name: str,
                   plan_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(plan_context, dict) or not plan_context:
            return {
                "matched": False,
                "reason": "no_recent_plan",
                "plan_id": None,
                "step_id": None,
            }

        steps = plan_context.get("steps", [])
        if not isinstance(steps, list):
            steps = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            if step.get("action_name") == action_name:
                return {
                    "matched": True,
                    "reason": "action_found_in_recent_plan",
                    "plan_id": plan_context.get("plan_id"),
                    "step_id": step.get("step_id"),
                    "description": step.get("description"),
                }

        return {
            "matched": False,
            "reason": "action_not_in_recent_plan",
            "plan_id": plan_context.get("plan_id"),
            "step_id": None,
        }

    def _metadata(self, action_name: str) -> Dict[str, Any]:
        if hasattr(self.registry, "get_metadata"):
            return self.registry.get_metadata(action_name)
        return {}

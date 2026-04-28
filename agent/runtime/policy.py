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

        next_action = plan_context.get("next_action")
        if isinstance(next_action, dict) and next_action.get("action_name") == action_name:
            return {
                "matched": True,
                "reason": "action_found_in_next_action",
                "plan_id": plan_context.get("plan_id"),
                "step_id": (
                    next_action.get("step_id")
                    or plan_context.get("current_step_id")
                ),
                "description": next_action.get("description"),
            }

        steps = plan_context.get("steps", [])
        if not isinstance(steps, list):
            steps = []
        allowed_action = ActionPolicy._find_allowed_action(
            action_name,
            plan_context.get("allowed_actions"),
        )
        if allowed_action is not None:
            step = ActionPolicy._find_step_match(action_name, steps)
            return {
                "matched": True,
                "reason": "action_found_in_allowed_actions",
                "plan_id": plan_context.get("plan_id"),
                "step_id": (
                    allowed_action.get("step_id")
                    or (step or {}).get("step_id")
                    or plan_context.get("current_step_id")
                ),
                "description": (
                    allowed_action.get("description")
                    or (step or {}).get("description")
                ),
            }

        step = ActionPolicy._find_step_match(action_name, steps)
        if step is not None:
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

    @staticmethod
    def _find_allowed_action(action_name: str, allowed_actions) -> Optional[Dict[str, Any]]:
        if not isinstance(allowed_actions, list):
            return None
        for item in allowed_actions:
            if isinstance(item, dict):
                if item.get("action_name") == action_name:
                    return item
            elif item == action_name:
                return {"action_name": item}
        return None

    @staticmethod
    def _find_step_match(action_name: str, steps: list) -> Optional[Dict[str, Any]]:
        for step in steps:
            if not isinstance(step, dict):
                continue
            if step.get("action_name") == action_name:
                return step
            allowed_actions = step.get("allowed_actions")
            if isinstance(allowed_actions, list) and action_name in allowed_actions:
                return step
        return None

    def _metadata(self, action_name: str) -> Dict[str, Any]:
        if hasattr(self.registry, "get_metadata"):
            return self.registry.get_metadata(action_name)
        return {}

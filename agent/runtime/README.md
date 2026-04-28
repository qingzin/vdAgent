# Runtime Adapter PoC

This package is the first migration seam for a future nanobot-based runtime.
It does not depend on nanobot yet. The goal is to protect vdAgent's existing
GUI and chassis-domain actions while exposing them through a runtime-neutral
tool interface.

## Current Scope

- Export `ActionRegistry` tools as nanobot/MCP-friendly descriptors.
- Execute low-risk read-only tools directly.
- Return a confirmation request for medium/high-risk or side-effectful tools.
- Require a matching `confirmation_id` and unchanged `params_digest` before a
  confirmation-required tool can execute.
- Block direct runtime calls to hidden registry actions where `exposed=False`.
- Route complex chassis goals to planning/knowledge tools before write actions.
- Map the existing JSONL memory store into session, history, and knowledge
  layers.
- Prefer explainable ranked experience recall when the memory store supports
  it, while falling back to legacy query/recent recall for older stores.

## Ranked Experience Recall

`NanobotMemoryBridge.recall_experiences(...)` first tries
`rank_experience_seeds(...)`. Ranked results include `match_score` and
`match_reasons`, so `handle_user_goal(...)` can return planner-ready recall
context without changing the tool execution flow.

The scorer is deterministic and dependency-free. It gives small bonuses for
condition exact matches, action matches, keyword hits in experience fields,
positive outcome wording, and higher numeric confidence.

## Plan Step Schema

Planning tools still return the existing readable Markdown for UI callers, but
the saved plan dict now carries a small executable context:

- `current_step_id`: the step currently selected as the next executable unit.
- `next_action`: a dict with `action_name`, `step_id`, `description`,
  `params_needed`, `risk_level`, and `validation`.
- `allowed_actions`: action names mentioned across the structured plan,
  including multiple actions found in a single recommended step.

The runtime records these fields in the `runtime_plan_context_saved` trace
payload and exposes the same summary as `RuntimeToolResult.metadata.plan_context`
when a planning tool is called through `handle_user_goal`.

## Confirmation Flow

Runtime tools are policy-checked before any callback is invoked.

1. The runtime first verifies that the action exists and is exposed.
2. Low-risk read-only tools (`risk_level="low"` and `side_effects=False`) run
   immediately.
3. Medium-risk, high-risk, or side-effectful tools return
   `status="requires_confirmation"` without calling the action callback.
4. The confirmation response includes `metadata.policy_decision`, with a
   `confirmation_id`, `params_digest`, and `plan_match` summary.
5. To execute the action, call the same tool again with unchanged params,
   `confirmed=True`, and the matching `confirmation_id`.
6. Missing, unknown, mismatched, or stale confirmation ids return
   `status="error"` and do not call the action callback.

## Non-goals

- No full autonomous multi-step executor.
- No direct nanobot package dependency.
- No change to `main.py`, `AgentContext`, or existing GUI attach flow.
- No replacement of the existing safety confirmation behavior.

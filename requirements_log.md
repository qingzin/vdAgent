# Requirements Log

## 2026-04-28 - Structured planning context and experience retrieval

- Add a stable structured planner schema with `plan_id`, `goal`, `condition_name`, `steps`, `validation_metrics`, and `required_confirmation`, while keeping existing readable planning text for the UI.
- Let the executor save the latest planning context after read-only planning actions, continue to require confirmation for high-risk or side-effect actions, and warn when a requested action is not matched to the latest plan.
- Extend engineering experience seeds with optional planning, setup, metric, feedback, outcome, and confidence fields.
- Add filtered memory retrieval by `condition_name`, `action_name`, and keyword, and make planning/knowledge actions prefer relevant experience recall.
- Cover the behavior with pytest tests that avoid GUI and hardware dependencies.

Conflict/reasonableness check: this aligns with the existing single-tool executor design because it adds context and confirmation guidance without introducing an autonomous multi-step executor, third-party dependencies, or GUI flow changes.

## 2026-04-28 - Nanobot migration runtime PoC

- Add a runtime adapter seam under `agent/runtime/` so vdAgent actions can be exposed as nanobot/MCP-friendly tools without replacing the current GUI flow.
- Preserve existing safety behavior: low-risk read-only tools execute directly, while medium/high-risk or side-effectful tools return a confirmation request unless explicitly confirmed.
- Add a nanobot-style memory bridge over the existing JSONL store, grouped as session, history, and knowledge layers.
- Add a PoC route where complex chassis goals are handled by planning/knowledge tools first instead of directly calling write actions.
- Keep this as an integration seam only: no nanobot dependency, no autonomous multi-step executor, and no `main.py` changes.

Conflict/reasonableness check: this is compatible with the structured planning context work because it reuses plan context without changing planner output or GUI flow.

## 2026-04-28 - Runtime safety boundary hardening

- Add a minimal runtime action policy that only allows existing actions with `exposed=True`, distinguishes direct execution from confirmation-required actions, and reports plan-match context.
- Replace the old `confirmed=True` bypass with a two-step confirmation flow: first request returns `confirmation_id` and `params_digest`, and execution requires the same id with unchanged params.
- Ensure hidden actions cannot be invoked directly through the runtime even if the caller knows the action name.
- Preserve compatibility for low-risk read-only tools and keep `confirmed=True` available only as part of the validated confirmation flow.
- Add tests for hidden action blocking, high-risk confirmation id validation, medium/side-effect confirmation requirements, suggest routing, and knowledge layer export.

Conflict/reasonableness check: this deliberately tightens the earlier runtime PoC behavior where `confirmed=True` alone was enough. The change is reasonable because it preserves the public call shape while closing a runtime safety bypass, and it avoids new dependencies, schema changes, or GUI changes.

## 2026-04-28 - Executable plan next action schema

- Extend planner dicts with `current_step_id`, `next_action`, and `allowed_actions` so the runtime can identify the smallest executable next action without changing existing readable plan text.
- Make schema normalization detect multiple action names mentioned inside one recommended step and expose all of them through `allowed_actions`.
- Persist `current_step_id`, `next_action`, and `allowed_actions` in runtime plan-context trace payloads, and expose the same summary through planning tool metadata.
- Make runtime policy plan matching prefer `next_action` and `allowed_actions`, while keeping legacy `steps` matching as a fallback.
- Cover planner schema, runtime metadata visibility, and policy matching priority with tests.

Conflict/reasonableness check: this is compatible with the prior structured planning and runtime safety work because it enriches existing plan context instead of adding autonomous execution, new dependencies, or GUI changes.

## 2026-04-28 - Explainable ranked experience recall

- Keep the existing `query_experience_seeds(...)` filter behavior unchanged for compatibility.
- Add ranked recall through `rank_experience_seeds(...)`, returning each recalled seed with `match_score` and `match_reasons`.
- Score condition exact matches, action matches, keyword hits in goal/objective/lesson/result/user_feedback/outcome/params/metrics, positive outcome wording, and numeric confidence.
- Make runtime, planning, and knowledge recall prefer ranked recall, with fallback to query/recent memory when a store does not support ranking.
- Ensure `handle_user_goal(...)` exposes ranked `recalled_experiences` for later planner use, and keep planning/knowledge actions safe with empty or unavailable memory.

Conflict/reasonableness check: this is a minimal deterministic scorer over the existing JSONL memory. It avoids new dependencies and does not replace the current planner, runtime policy, storage format, or GUI flow.

## 2026-04-28 - Enriched experience seed context

- Extend engineering experience seeds with optional `plan_id`, `step_id`,
  `plan_goal`, and `next_action` fields so later recall can connect an action
  result to the plan step that produced it.
- Make executor and runtime writes include available recent plan context without
  changing existing seed fields.
- Let the runtime capture best-effort `get_current_setup` before/after snapshots
  for configuration-changing tuning actions. Snapshot failures are ignored and
  never block the primary action.

Conflict/reasonableness check: this strengthens learning trace quality while keeping the JSONL store, GUI flow, and action execution semantics unchanged.

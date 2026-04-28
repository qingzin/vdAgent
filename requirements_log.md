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

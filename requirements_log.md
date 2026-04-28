# Requirements Log

## 2026-04-28 - Structured planning context and experience retrieval

- Add a stable structured planner schema with `plan_id`, `goal`, `condition_name`, `steps`, `validation_metrics`, and `required_confirmation`, while keeping existing readable planning text for the UI.
- Let the executor save the latest planning context after read-only planning actions, continue to require confirmation for high-risk or side-effect actions, and warn when a requested action is not matched to the latest plan.
- Extend engineering experience seeds with optional planning, setup, metric, feedback, outcome, and confidence fields.
- Add filtered memory retrieval by `condition_name`, `action_name`, and keyword, and make planning/knowledge actions prefer relevant experience recall.
- Cover the behavior with pytest tests that avoid GUI and hardware dependencies.

Conflict/reasonableness check: this aligns with the existing single-tool executor design because it adds context and confirmation guidance without introducing an autonomous multi-step executor, third-party dependencies, or GUI flow changes.

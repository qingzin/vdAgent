# Requirements Log

## 2026-04-28 - Structured planning context and experience retrieval

- Add a stable structured planner schema with `plan_id`, `goal`, `condition_name`, `steps`, `validation_metrics`, and `required_confirmation`, while keeping existing readable planning text for the UI.
- Let the executor save the latest planning context after read-only planning actions, continue to require confirmation for high-risk or side-effect actions, and warn when a requested action is not matched to the latest plan.
- Extend engineering experience seeds with optional planning, setup, metric, feedback, outcome, and confidence fields.
- Add filtered memory retrieval by `condition_name`, `action_name`, and keyword, and make planning/knowledge actions prefer relevant experience recall.
- Cover the behavior with pytest tests that avoid GUI and hardware dependencies.

Conflict/reasonableness check: this aligns with the existing single-tool executor design because it adds context and confirmation guidance without introducing an autonomous multi-step executor, third-party dependencies, or GUI flow changes.

## 2026-05-01 - Agent history bounds and recovery verification

- Fix the agent conversation history so it remains bounded by both message count and estimated token/character budget.
- Ensure long user inputs and long action/tool results are truncated before they are retained in LLM history, while preserving full UI-facing action results.
- Verify recovery behavior for long input, long action result, LLM 400/context overflow, and LLM timeout paths.
- Identify the git commit associated with the history-size-control regression using git history output rather than speculation.

Conflict/reasonableness check: this is scoped to executor/LLM recovery behavior and test coverage. It does not require a new dependency, schema change, governance policy change, or model configuration change.

## 2026-05-02 - Repository history and code issue analysis

- Review the current project's commit history and code structure.
- Identify existing problems from maintainability, correctness, testing, and repository hygiene perspectives.
- Keep the work to analysis and requirement logging unless a separate fix is requested.

Conflict/reasonableness check: this is a read-only audit request except for the required requirements log update. It does not conflict with prior scoped implementation requests and does not require dependency, public API, schema, or governance changes.

## 2026-05-06 - Confirmation flow QThread deletion crash

- Fix the crash after confirming a compound agent action when the previous worker thread wrapper has already been deleted by Qt.
- Preserve the existing confirmation and multi-step execution behavior while making worker/thread cleanup idempotent.
- Add regression coverage for retrying `_call_llm` after the stored QThread wrapper raises `RuntimeError` on lifecycle access.

Conflict/reasonableness check: this is a localized executor lifecycle fix and test update. It does not require a new dependency, public API change, database schema change, governance policy change, or feature deletion.

## 2026-05-06 - Repeated confirmation dialog visibility

- Fix the issue where the confirmation dialog does not appear on the third confirmed operation.
- Keep the existing non-modal confirmation flow and multi-step execution behavior.
- Avoid reusing a hidden Qt dialog instance across repeated confirmations if that instance can become invisible or stale.

Conflict/reasonableness check: this is scoped to the chat UI confirmation dialog lifecycle. It does not require a new dependency, public API change, database schema change, governance policy change, or feature deletion.

## 2026-05-06 - Dependency installation expectation

- When a dependency already declared by the project is missing from the local environment, install it directly and continue validation instead of skipping or substituting another approach.
- Keep the existing confirmation rule for adding a new third-party dependency that is not already declared by the project.

Conflict/reasonableness check: this refines the workflow for environment setup. It is compatible with the existing rule to stop before introducing new undeclared third-party dependencies.

## 2026-05-06 - Development roadmap from commit history

- Review the full project commit history and current code structure.
- Identify the current development phase, recurring problem areas, and likely technical debt.
- Propose the next development direction from maintainability, reliability, product value, and testing perspectives.

Conflict/reasonableness check: this is an analysis and planning request plus the required requirements log update. It does not require a new dependency, public API change, database schema change, governance policy change, or feature deletion.

## 2026-05-06 - Explicit executor state and confirmation identity

- Make `agent/executor.py` use an explicit state model instead of inferring task state only from `_is_busy`, `_multi_step_active`, and `_pending_action`.
- Bind every confirmation request to a stable `confirmation_id`, action, params, summary, status, and result.
- Reject stale or mismatched confirmation/cancel events so old dialogs cannot execute the wrong pending operation.
- Keep future commit messages in Chinese.

Conflict/reasonableness check: this is a requested internal executor/UI contract change. It does not add dependencies, database schema changes, governance policy changes, or remove existing user-facing features.

## 2026-05-06 - Agent framework and execution state stabilization

- Evaluate whether adopting an open-source agent framework such as nanobot can improve the unstable agent execution state machine.
- Produce a detailed implementation plan for the first-priority execution-state stabilization work.
- Execute the implementation after resolving whether to introduce an external framework dependency or use a local runtime/state-machine layer.

Conflict/reasonableness check: this request may imply a new third-party dependency and may change the runtime boundary of the agent. Per project rules, the dependency/framework direction must be confirmed before implementation proceeds.

## 2026-05-07 - Query result completion and durable confirmation panel

- Fix read-only query actions showing only "完成" after the action result is fed back into the LLM continuation loop.
- Add a stable read-only `get_system_status` action for querying the current simulator/agent-visible state.
- Make the chat panel contain a persistent confirmation strip as the primary confirmation UI, with the floating dialog kept only as an auxiliary reminder.
- Preserve step-by-step confirmation for multi-action requests such as platform offset, scene change, and anti-roll bar changes.

Conflict/reasonableness check: this implements the confirmed local plan. It does not introduce dependencies, change database schemas, alter governance policy definitions, or remove existing user-facing features.

## 2026-05-07 - State-machine driven multi-step action queue

- Fix multi-turn LLM degradation where the model emits confirmation-looking text instead of structured tool calls after several agent interactions.
- Add an executor-owned action queue so multi-step requests are parsed once, then confirmed and executed step by step without asking the LLM to remember remaining work after each action.
- Add an internal `submit_action_plan` protocol tool for structured multi-action plans, plus protocol-error handling for non-structured pseudo confirmation text.
- Preserve single-action confirmation, read-only direct query behavior, stale confirmation rejection, and the chat confirmation panel.

Conflict/reasonableness check: this is a local runtime/state-machine change chosen to avoid adding an external framework dependency. It does not change external device, CarSim, database, or governance interfaces.

## 2026-05-07 - Read-only context actions and pending-confirmation text

- Fix modification requests such as "前轮弹簧刚度降低5%" where the LLM first calls a read-only setup query to calculate the target value.
- Treat read-only actions as intermediate context when the original user message clearly expresses a mutation intent, while preserving direct return for explicit status/query requests.
- Convert model text like `待用户确认 set_spring({...})` into a real confirmation request instead of ending the flow as a normal assistant reply.
- Stop the extra LLM continuation after a confirmed single direct action; the executor can finish deterministically after action completion.

Conflict/reasonableness check: this refines the local executor protocol handling introduced by the action queue work. It does not add dependencies or change external device, CarSim, database, or governance interfaces.

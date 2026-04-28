# Runtime Adapter PoC

This package is the first migration seam for a future nanobot-based runtime.
It does not depend on nanobot yet. The goal is to protect vdAgent's existing
GUI and chassis-domain actions while exposing them through a runtime-neutral
tool interface.

## Current Scope

- Export `ActionRegistry` tools as nanobot/MCP-friendly descriptors.
- Execute low-risk read-only tools directly.
- Return a confirmation request for medium/high-risk or side-effectful tools.
- Route complex chassis goals to planning/knowledge tools before write actions.
- Map the existing JSONL memory store into session, history, and knowledge
  layers.

## Non-goals

- No full autonomous multi-step executor.
- No direct nanobot package dependency.
- No change to `main.py`, `AgentContext`, or existing GUI attach flow.
- No replacement of the existing safety confirmation behavior.

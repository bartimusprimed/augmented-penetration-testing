# Decision Log: Augmented Penetration Testing (APT)

> Maintained by the [Architect Agent](.github/agents/architect.md).
> Every non-trivial architectural choice gets an entry here.
> One-way-door decisions require explicit user sign-off before the choice is enacted.

---

## How to Use

1. The Architect Agent appends an entry for every non-trivial decision.
2. Two-way-door decisions: decide fast, move on.
3. One-way-door decisions: surface to the Orchestrator → get explicit user sign-off → then proceed.
4. Each entry must include a revisit trigger so decisions don't calcify into unquestioned defaults.

---

## Decision: Module variable system — string keys over typed fields

**Date:** 2026-04-15
**Context:** Modules need to declare prerequisites and outputs so the chain executor can validate ordering and compose DAG steps. Two options: (A) typed fields on Target, (B) open string keys in a `variables: dict[str, Any]` store with a `VariableKey` helper for well-known names.
**Options considered:**
- A: Add typed boolean/list fields directly to Target (e.g. `is_alive`, `ports`) — already partially done
- B: Generic `variables: dict[str, Any]` on Target + `VariableKey` helper in `module_metadata.py` for canonical names

**Choice:** B (generic variable map + VariableKey helper)
**Reason:** Option A requires modifying Target every time a new module type is introduced. Option B is open-closed: new modules can introduce new variable keys without touching the core model. The helper constants prevent typo bugs in common keys.
**Reversibility:** Two-way door — can migrate back to typed fields if the open string approach proves hard to maintain.
**Revisit trigger:** When more than 20 distinct variable keys exist and discoverability becomes a problem.

---

## Decision: Chain model — DAG over ordered list

**Date:** 2026-04-15
**Context:** The original `Chain.module_keys: list[str]` model forces sequential execution and manual ordering. Caldera-style attack chaining requires parallel execution of independent steps and dependency-aware sequencing.
**Options considered:**
- A: Keep list, add priority/weight field per entry
- B: Replace with DAG: `nodes: dict[str, ChainNode]` + `edges: list[tuple[str, str]]`

**Choice:** B (DAG)
**Reason:** A DAG naturally represents prerequisite relationships. Topological sort gives correct execution order for free. Option A would require rebuilding the same logic manually.
**Reversibility:** One-way door for the model schema — existing `Chain` serialization changes. `module_keys` is kept as a derived property for backward compatibility with any code reading it as a list.
**Revisit trigger:** If the drag-and-drop canvas proves too complex for users and they prefer a simpler list-based flow.

---

## Decision: C2 transport — HTTP polling over WebSocket/raw TCP

**Date:** 2026-04-15
**Context:** The beacon needs to communicate with the APT C2 server. Options: (A) HTTP polling (checkin/result), (B) persistent WebSocket, (C) raw TCP.
**Options considered:**
- A: HTTP polling — simple, works through most firewalls, easy to implement in pure stdlib Python
- B: WebSocket — lower latency, requires `websockets` dependency on beacon
- C: Raw TCP — minimal overhead, harder to implement reliably, firewall-unfriendly

**Choice:** A (HTTP polling)
**Reason:** The beacon must be deployable as a self-contained Python script with zero non-stdlib dependencies. HTTP polling satisfies this. Latency from the polling interval is acceptable for attack-chain orchestration use cases.
**Reversibility:** Two-way door — the protocol module is isolated, transport can be swapped.
**Revisit trigger:** When sub-second command latency is required.

---

## Decision: TWIAYN agents as development workflow

**Date:** 2026-04-15
**Context:** Three prior iterations of this project (tpott → apt → augmented-penetration-testing) each drifted from the intended Caldera-style architecture. A structured development workflow is needed to prevent future drift.
**Options considered:**
- A: Ad-hoc development with no formal workflow
- B: Adopt TWIAYN (This Workflow Is All You Need) — Orchestrator + specialist agents + approval gates

**Choice:** B (TWIAYN)
**Reason:** TWIAYN's pre-flight checklist, approval gates, and TDD enforcement directly address the drift problem. The agent roster (Orchestrator, Inquiry, Architect, Implementor, Tester, Reviewer, Feature Planner) maps cleanly to the development stages needed for APT.
**Reversibility:** Two-way door — the workflow docs are additive and do not change code.
**Revisit trigger:** If the approval gate overhead significantly slows development velocity.

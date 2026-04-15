# Workflow: New Project

Use this workflow when starting from a blank or near-blank repository.

### Agents Involved

| Phase | Agent | File |
|---|---|---|
| Phase 0 — Product Brief | Inquiry Agent | [`.github/agents/inquiry.md`](../.github/agents/inquiry.md) |
| Phase 1 — Inquiry | Inquiry Agent | [`.github/agents/inquiry.md`](../.github/agents/inquiry.md) |
| Phase 2 — Architecture | Architect Agent | [`.github/agents/architect.md`](../.github/agents/architect.md) |
| Phase 3 — Core Loop | Implementor Agent + Tester Agent | [`.github/agents/implementor.md`](../.github/agents/implementor.md), [`.github/agents/tester.md`](../.github/agents/tester.md) |
| All phases | Orchestrator Agent | [`.github/agents/orchestrator.md`](../.github/agents/orchestrator.md) |

---

## Phase 0 — Product Brief

**Goal:** Confirm the problem worth solving before any technical scoping begins.

Ask the user exactly these five questions. Get answers before moving to Phase 1.

1. **Problem** — Whose pain are we solving, in one sentence?
2. **Why now** — What changed? What evidence or trigger exists? What is the cost of waiting?
3. **Assumptions** — What are we taking as true that has not been validated?
4. **Success metric** — The one number we expect to move.
5. **Reversibility** — Is this a one-way door (costly to undo) or a two-way door (easily reversed)?

**Gate:** Present answers as a Product Brief summary. Wait for explicit confirmation before Phase 1.

---

## Phase 1 — Inquiry

**Goal:** Understand the project before touching any code.

1. **Purpose** — What problem does this solve? Who uses it?
2. **Platform** — Local machine, cloud hosted, embedded, or mixed?
3. **Tech stack** — Web app, native binary, interpreted scripts, or other?
4. **Coding practice** — OOP, functional, procedural, or mixed?
5. **State management** — User config, database, reactive UI, in-memory, or none?
6. **Interaction mechanism** — Web browser, CLI, native UI, game engine, API, or other?

Ask all six questions in one message. Do not drip them.

---

## Phase 2 — Architecture Deliverable

**Goal:** Produce a written plan the user approves before any code is written.

Fill in [`templates/architecture.md`](../templates/architecture.md). Commit as `ARCHITECTURE.md`. Present to user. Wait for approval. Only then proceed to Phase 3.

---

## Phase 3 — Core Loop Implementation

**Goal:** Build only the core loop. Nothing else.

- Implement only `[CORE]` features from the approved architecture.
- Structure modularly. Run and confirm core loop works.
- Write one smoke test.
- Commit. Ask user to verify before continuing.

# Workflow: Add Feature

Use this workflow when the core project loop exists and new functionality is requested.
This is the **default workflow** after project creation is complete.

### Agents Involved

| Step | Agent |
|---|---|
| Step 0 — Product Brief | Feature Planner Agent |
| Step 1 — Feature Breakdown | Feature Planner Agent |
| Step 2 — Architecture Check | Architect Agent |
| Step 3 — Approval Gate | Orchestrator Agent |
| Step 4a — Write Tests (red) | Tester Agent |
| Step 4b — Implement Feature (green) | Implementor Agent |
| Step 4c — Update Architecture | Architect Agent |
| Step 5 — Integration Tests | Tester Agent |
| Step 6 — Report Back | Orchestrator Agent |

---

## Step 0 — Product Brief

Confirm the problem is worth solving. For the incoming request, confirm:
1. Problem — Whose pain, in one sentence?
2. Why now — What changed?
3. Assumptions — 2–3 per feature.
4. Success metric — The one number we expect to move.
5. Reversibility — One-way or two-way door?

**Gate:** Present Product Brief. Wait for explicit confirmation before Step 1.

---

## Step 1 — Feature Breakdown

Split the request into the smallest individually deliverable units. Present list to user. Confirm before continuing.

---

## Step 2 — Architecture Check

Read `ARCHITECTURE.md`. For each feature: check for conflicts, prefer expansion over new files, note simplifications. Report findings. Wait for approval if arch changes are needed.

---

## Step 3 — Approval Gate

Present concise plan. **Do not write code until the user approves.**

---

## Step 4 — Test First, Then Implement

For each approved feature:

### 4a. Write tests (red state)
Write unit tests. Verify they fail. Commit.

### 4b. Implement (green state)
Write simplest code that makes tests pass. Commit.

### 4c. Update `ARCHITECTURE.md`
Change `[NOT IMPLEMENTED]` → `[IMPLEMENTED]`. Add new entries if needed.

---

## Step 5 — Integration Tests

Write end-to-end tests matching how a real user interacts with the feature. All tests must pass.

---

## Step 6 — Report Back

Tell the user: features added, test counts, simplifications, next action.

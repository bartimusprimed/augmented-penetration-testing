# Workflow: Project Review / Cleanup

Use this workflow when the codebase needs optimization or simplification — not new features.

### Agents Involved

| Step | Agent |
|---|---|
| Steps 1–3 | Reviewer Agent |
| Step 4 (code changes) | Implementor Agent |
| Step 5 (report) | Orchestrator Agent |

---

## Step 1 — Audit

Read the entire codebase. Look for: dead code, duplication, overcomplexity, unclear naming, test gaps, dependency bloat. Do not change anything yet.

---

## Step 2 — Present the Plan

For each proposed change: What, Why, Risk (low/medium/high). Group by risk. Present high-risk separately. **Do not proceed until the user approves the plan.**

---

## Step 3 — Track Changes

Create or append to `SIMPLIFICATIONS.md`. For each change:

```markdown
## YYYY-MM-DD — <short title>
**File:** `path/to/file`
**Change:** What was changed and why.
**Revert:** What to restore if a regression is found.
```

Commit `SIMPLIFICATIONS.md` before making any code changes.

---

## Step 4 — Apply Changes

Apply one logical group at a time. Run full test suite after each. If tests fail: revert + document. If pass: commit.

---

## Step 5 — Report Back

What changed, before/after metrics, what was skipped and why, link to `SIMPLIFICATIONS.md`.

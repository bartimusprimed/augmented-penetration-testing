# Architecture: Augmented Penetration Testing (APT)

> This document is the single source of truth for project architecture.
> Update it whenever features are added, changed, or removed.
> All agents must read this before writing any code.

---

## Purpose

APT (Augmented Penetration Testing) is a desktop application built with Flet (Python/Flutter) that gives penetration testers a Caldera-style attack-chain builder with a native UI. Users discover targets, compose attack chains by dragging-and-dropping modules onto a canvas, and execute those chains — in order, with dependency checking — against one or many targets. A built-in C2 server manages remote agents so that chain steps can execute on the target host rather than the operator machine.

---

## Problem Statement

Penetration testers waste time manually sequencing tools and lose track of intermediate results; APT automates attack-chain execution with prerequisite/postrequisite awareness, reducing a multi-hour manual workflow to a drag-and-drop composition in minutes.

---

## Success Metrics

| Metric | Value |
|---|---|
| North-star metric | Chains with ≥ 2 steps execute end-to-end without manual intervention |
| Baseline | 0 (chains are currently lists with no dependency checking) |
| Expected direction & size | 100% of well-formed chains execute without operator intervention |
| Time horizon | After Phase 4 completion |
| Guardrail metrics | All 12 existing Flet API compat tests continue to pass |

---

## Assumptions

| Assumption | Status | Owner |
|---|---|---|
| Flet 0.84.0 API is stable for this work | `validated` | |
| Modules can declare string "fact" keys for prerequisites | `assumed` | |
| The HTTP C2 (beacon/checkin) is sufficient for chain tasking | `assumed` | |
| Drag-and-drop via ft.Draggable/ft.DragTarget works for the canvas | `assumed` | |
| Python ≥ 3.10 is available on operator machines | `validated` | |

---

## Configuration

| Dimension | Decision | Notes |
|---|---|---|
| Platform | Local desktop (macOS, Linux, Windows) | No cloud dependency |
| Tech stack | Python + Flet 0.84.0 (Flutter renderer) | |
| Coding practice | OOP + functional components | `@ft.component` for UI, `@ft.observable` for state |
| State management | Reactive in-memory (`@ft.observable`) | No persistence yet |
| Interaction mechanism | Native UI (Flet/Flutter) | |

---

## Core Loop

User adds a target IP → selects modules and drags them onto a chain canvas → APT validates prerequisites (variable dependency completeness) → user clicks Run → APT executes nodes in topological order on a Flet-managed thread → results and discovered variables flow back to the Target model and C2 session view.

---

## Features

| Feature | Status | Module / File | Notes |
|---|---|---|---|
| Target management (add/remove/select) | `[IMPLEMENTED]` | `src/models/target.py`, `src/components/targets/` | |
| Module loader (dynamic discovery) | `[IMPLEMENTED]` | `src/utils/module_loader.py` | |
| Module execution against targets | `[IMPLEMENTED]` | `src/models/apt.py` | |
| Chain model (ordered list) | `[IMPLEMENTED]` | `src/models/chain.py` | |
| Chain builder UI (DAG canvas + palette) | `[IMPLEMENTED]` | `src/components/chains/chain_canvas.py`, `src/components/chains/module_palette.py` | |
| HTTP C2 server + beacon module | `[IMPLEMENTED]` | `src/c2/server.py`, `src/modules/command_and_control/beacon.py` | |
| Module variable system (consumes/provides) | `[IMPLEMENTED]` | `src/modules/base_module.py`, `src/models/module_metadata.py` | Phase 0 |
| Target variable store | `[IMPLEMENTED]` | `src/models/target.py` | Phase 0 |
| Chain as DAG (nodes + edges) | `[IMPLEMENTED]` | `src/models/chain.py`, `src/models/chain_node.py` | Phase 1 |
| Topological chain execution | `[IMPLEMENTED]` | `src/models/apt.py` | Phase 1 |
| Prerequisite validation | `[IMPLEMENTED]` | `src/models/apt.py` | Phase 1 |
| Drag-and-drop chain canvas | `[IMPLEMENTED]` | `src/components/chains/chain_canvas.py` | Phase 2 |
| Chain node cards with variable pills | `[IMPLEMENTED]` | `src/components/chains/chain_node_card.py` | Phase 2 |
| C2 session management view | `[IMPLEMENTED]` | `src/views/c2_view.py`, `src/components/c2/` | Phase 3 |
| Session variable tracking (server-side) | `[IMPLEMENTED]` | `src/c2/server.py` | Phase 3 |
| Module-aware C2 tasking | `[IMPLEMENTED]` | `src/c2/protocol.py` | Phase 4 |
| Report export | `[NOT IMPLEMENTED]` | | Planned |
| Persistence (save/load chains) | `[IMPLEMENTED]` | `src/models/apt.py`, `.apt/chains.json` | |
| Agent installer/dropper | `[NOT IMPLEMENTED]` | | Planned |

---

## File Structure

```
src/
  main.py                          # Entry point — ft.run(render_app)
  c2/
    protocol.py                    # Message dataclasses (CheckinMessage, TaskMessage, ResultMessage)
    server.py                      # HTTP C2 server, session management, variable tracking
  models/
    apt.py                         # Root state — targets, modules, chains; run_chain (topological)
    chain.py                       # Chain DAG model (nodes dict + edges list)
    chain_node.py                  # ChainNode dataclass (module_key, position, status)
    module_metadata.py             # AttackTactic, TargetOS, TargetArch, VariableKey constants
    target.py                      # Target observable — ip, status, activity_log, variables map
  modules/
    base_module.py                 # APT_MODULE ABC — consumes_variables/produces_variables + OS hooks
    reconnaissance/arpping.py      # ARP ping example module
    command_and_control/beacon.py  # C2 beacon module — produces ["c2_session"]
    [tactic]/[module].py           # Additional modules per MITRE tactic
  utils/
    module_loader.py               # Dynamic module discovery
    permissions.py                 # Raw socket access check
  components/
    app/navbar.py                  # Navigation sidebar
    home/                          # Home view components
    targets/                       # Target card, list, actions
    modules/                       # Module card, list
    chains/
      chain_canvas.py              # Drag-drop DAG canvas (Phase 2)
      chain_node_card.py           # Draggable node widget with variable pills (Phase 2)
      module_palette.py            # Module palette sidebar
      chain_card.py                # Chain list entry card
    c2/
      session_table.py             # Agent roster table (Phase 3)
      agent_detail.py              # Per-agent detail panel (Phase 3)
  views/
    app_view.py                    # Root view — navigation + page routing
    home_view.py
    targets_view.py
    modules_view.py
    chains_view.py                 # Chains page (canvas + palette + chain list)
    settings_view.py
    c2_view.py                     # C2 session management page (Phase 3)
.github/
  copilot-instructions.md          # APT-specific coding conventions
  agents/                          # TWIAYN specialist agents
  workflows/                       # CI/CD (tests.yml, update-architecture-diagram.yml)
workflows/                         # TWIAYN agent workflow playbooks
templates/                         # TWIAYN document templates
ARCHITECTURE.md                    # This file
DECISIONS.md                       # Architectural decision log
```

---

## Dependencies

| Name | Version | Purpose |
|---|---|---|
| flet | 0.84.0 | UI framework (Flutter-backed Python) |
| scapy | ≥ 2.7.0 | Raw packet operations (lazy-imported in modules) |
| cryptography | optional | AES-GCM encryption for C2 channel |
| pytest | dev | Test runner |

---

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-15 | Initial ARCHITECTURE.md created covering Phases 0–4 | Copilot |

---

## Decision Log

Non-trivial architectural decisions are tracked in [`DECISIONS.md`](DECISIONS.md). See that file for the full record of one-way-door and significant two-way-door decisions.

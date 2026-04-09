# APT – GitHub Copilot Instructions

## What is APT?

APT (Augmented Penetration Testing) is a desktop/mobile application built with [Flet](https://flet.dev) (Python UI framework).  
Its purpose is to wrap arbitrary Python scripts (modules) into a repeatable, auditable environment: the user selects targets (IP addresses), enables modules, then runs those modules against the targets. APT handles threading, status updates, and activity logging so module authors only need to implement their core logic.

---

## Project Layout

```
src/
  main.py               # Entry point – calls ft.run(render_app)
  models/
    target.py           # Target observable dataclass + MESSAGE_TYPE enum
    apt.py              # Root application state (targets list + module loader)
  modules/
    base_module.py      # Abstract base class APT_MODULE
    arpping.py          # Example concrete module
  utils/
    module_loader.py    # Dynamically imports all modules in src/modules/
  components/           # Reusable @ft.component UI pieces
    app/
      navbar.py
    home/
      hero.py
      workflow.py
    targets/
      actions.py        # Enabled-module action buttons
      add.py            # Add-target text field
      context.py        # Context row shown when targets are selected
      list.py           # GridView of all target cards
      target.py         # Single target card
  views/                # Full-page @ft.component views
    app_view.py         # Root view – owns all pages + navigation
    home_view.py
    targets_view.py
    modules_view.py
    settings_view.py
  assets/
    icon.png
    splash.png
```

All Python source lives under `src/`. Flet resolves imports relative to that directory, so there are **no `__init__.py` files** and imports look like `from models.target import Target`.

---

## Framework – Flet

[Flet](https://flet.dev) is a Flutter-backed Python UI toolkit. Key APIs used in this project:

| API | Purpose |
|-----|---------|
| `@ft.component` | Declare a functional UI component (like a React component) |
| `@ft.observable` | Make a class reactive – UI re-renders when its fields change |
| `@dataclass` | Used together with `@ft.observable` on model classes |
| `ft.use_state(initial)` | Local state hook inside a `@ft.component`; returns `(value, setter)` |
| `ft.on_mounted(fn)` | Run `fn` once when the component mounts |
| `ft.context.page` | Access the current Flet `Page` from anywhere |
| `ft.context.page.render(lambda: component)` | Replace the current page content |
| `ft.context.page.show_dialog(dialog)` / `.pop_dialog()` | Show/dismiss an `ft.AlertDialog` |
| `e.page.run_thread(fn, arg)` | Run a blocking function on a background thread |

---

## Coding Patterns

### 1. Observable Models (`@ft.observable`)

Models are plain Python classes (or dataclasses) decorated with `@ft.observable`. Field changes automatically notify any UI component that reads those fields.

```python
import flet as ft
from typing import cast
from dataclasses import dataclass, field

@ft.observable
@dataclass
class MyModel:
    some_field: str = "default"
    items: list[str] = field(default_factory=list)

    def trigger_update(self):
        # Call when you mutate a mutable field (list, dict) directly
        # so observers are notified
        cast(ft.Observable, self).notify()
```

Use `update_field(name, value)` (as defined on `Target`) to set a field and log it, or assign directly for simple mutations.  
Call `trigger_update()` after batch-mutating list fields so the UI refreshes.

### 2. UI Components (`@ft.component`)

Every UI element is a plain Python function decorated with `@ft.component`. The function receives props as arguments and returns a Flet widget (or `None`/`ft.Container()` for empty views). Local state uses `ft.use_state`.

```python
import flet as ft
from models.apt import Apt

@ft.component
def MyComponent(state: Apt):
    count, set_count = ft.use_state(0)

    def increment(e: ft.Event[ft.Button]):
        set_count(count + 1)

    return ft.Column([
        ft.Text(f"Count: {count}"),
        ft.Button("Increment", on_click=increment)
    ])
```

- Component function names use **PascalCase** for exported components and **snake_case** for internal/helper components (see `target`, `target_list`, `add_target` vs `TargetActions`, `TargetContextActions`).
- Async event handlers are used where awaiting is needed (e.g., `async def handle(e): await something()`).

### 3. Views

Views are full-page `@ft.component` functions inside `src/views/`. They accept the root `Apt` state and compose components. Navigation is handled in `app_view.py` via `ft.context.page.render(lambda: page_component)`.

```python
import flet as ft
from models.apt import Apt

@ft.component
def MyView(state: Apt):
    return ft.Container(
        ft.Column([...]), expand=True
    )
```

### 4. Writing a New Module

Create a new `.py` file directly inside `src/modules/`. The file name **must match** the class name exactly (e.g., `mymodule.py` defines `class mymodule`). The module loader discovers and instantiates it automatically using this filename-equals-classname convention. Both the filename and class name use **lowercase/snake_case** (intentionally deviating from PEP 8 PascalCase for classes — see `arpping.py` as the canonical example).

```python
from modules.base_module import APT_MODULE
from models.target import Target, MESSAGE_TYPE


class mymodule(APT_MODULE):
    def __init__(self) -> None:
        super().__init__()

    def action(self, target: Target):
        # Import heavy dependencies (e.g. scapy) here – NOT at module top-level –
        # so the app starts fast and doesn't crash on import on restricted platforms.
        # from scapy.layers.inet import IP  # type: ignore

        # All module logic goes here.
        # Use target.log_activity() to report progress.
        target.log_activity("Starting my module...", True)

        # ... do the work ...

        target.log_activity("Done", True, MESSAGE_TYPE.SUCCESS)
        target.update_field("is_alive", True)

    def enable(self, e):
        self.enabled = e
```

`APT_MODULE.run()` wraps `action()` with `target.start_work()` / `target.finish_work()` bookending calls and activity-log banners. **Never override `run()`.**

`log_activity(msg, is_status_update=False, message_type=MESSAGE_TYPE.INFORMATION)`:
- Always appends `msg` to `target.activity_log`.
- When `is_status_update=True`, also updates `target.current_status` and `target.color_status`:
  - `MESSAGE_TYPE.SUCCESS` → green
  - `MESSAGE_TYPE.ERROR` → red
  - `MESSAGE_TYPE.INFORMATION` (default) → amber

### 5. Target Model

```python
# Key fields
target.ip_label        # str  – the IP address string
target.is_selected     # bool – user has selected this target
target.is_alive        # bool – set True when host responds
target.is_busy         # bool – True while a module is running on it
target.current_status  # str  – displayed on the target card
target.color_status    # ft.Colors – background of the card
target.activity_log    # list[str] – full history of log_activity() calls
target.ports           # list[int] – open ports found by scanning
```

### 6. Root State – `Apt`

`Apt` is the single root state object created once in `App`. It holds:
- `targets: list[Target]` – all tracked targets
- `modules: ModuleLoader` – loaded module classes
- Helper methods: `create_new_target`, `get_selected_targets`, `get_enabled_modules`, `run_action`, etc.

Pass `state: Apt` down to every component/view that needs it (prop-drilling; no global context object).

---

## Python Style Conventions

- **Python ≥ 3.10** – use `match`/`case` statements instead of long `if`/`elif` chains.
- **Type hints**: used on function signatures where helpful, but not exhaustively required; `# type: ignore` comments are acceptable for Flet internals.
- **Imports**: standard library first, then third-party (`flet`, `scapy`), then local (`models.*`, `components.*`, etc.).
- **Dataclasses**: use `@dataclass` with `field(default_factory=...)` for mutable defaults.
- **Logging**: use Python's standard `logging` module with `logging.log(logging.DEBUG, ...)` etc. Never use `print()` for debug output.
- **No `__init__.py` files** in `src/` or any of its subdirectories.
- **Async**: event handlers that need to `await` are defined as `async def`. Blocking I/O in module `action()` methods runs via `e.page.run_thread()` in `Apt.run_action`.
- **Comments**: only when explaining non-obvious logic; prefer self-documenting names.

---

## Running the App

> **Requirements**: Python ≥ 3.10, Flet ≥ 0.84.0, Scapy ≥ 2.7.0

```bash
# With uv (recommended)
uv run flet run src

# Or directly if flet is installed
flet run src
```

Dependencies are managed in `pyproject.toml`. To add a new dependency:

```bash
uv add <package>
```

---

## Architecture Diagram

The app has three high-level concerns that interact through the `Apt` state object:

```
Target Management  ←→  Module Management
       ↓
  Report Management
```

- **Target Management**: add/remove/view targets, track their status.
- **Module Management**: enable/disable modules, execute them against selected targets.
- **Report Management**: export results (planned).

Modules and Targets communicate via the `Target` observable object – a module reads `target.ip_label` and writes back via `target.log_activity()` and `target.update_field()`.

"""Tests to ensure Flet 0.84.0 API compatibility.

These tests guard against regressions that have broken the "Target Details"
dialog three times already:
  1. ft.Tab(text=...) — 'text' was renamed to 'label' in Flet 0.84.0
  2. ft.Tabs(tabs=[...]) — replaced by Tabs(content=..., length=...)
  3. ft.use_state() outside @ft.component — causes RuntimeError at runtime
"""

import ast
import os
import pathlib
import textwrap

import flet as ft
import pytest

SRC_DIR = pathlib.Path(__file__).resolve().parent.parent / "src"


# ---------------------------------------------------------------------------
# 1.  ft.Tab must accept 'label' (positional), NOT 'text'
# ---------------------------------------------------------------------------

class TestTabAPI:
    """Verify that ft.Tab uses the Flet 0.84.0 constructor signature."""

    def test_tab_rejects_text_keyword(self):
        """ft.Tab(text=...) must raise TypeError in Flet ≥ 0.84.0."""
        with pytest.raises(TypeError, match="text"):
            ft.Tab(text="Overview")

    def test_tab_accepts_label_positional(self):
        tab = ft.Tab("Overview")
        assert tab.label == "Overview"

    def test_tab_accepts_label_keyword(self):
        tab = ft.Tab(label="Shell")
        assert tab.label == "Shell"

    def test_tab_accepts_icon(self):
        tab = ft.Tab("Beacon", icon=ft.Icons.WIFI_TETHERING)
        assert tab.label == "Beacon"
        assert tab.icon is not None

    def test_tab_rejects_content_keyword(self):
        """ft.Tab no longer has a 'content' parameter in 0.84.0."""
        with pytest.raises(TypeError, match="content"):
            ft.Tab("X", content=ft.Container())


# ---------------------------------------------------------------------------
# 2.  ft.Tabs must use content + length, NOT tabs=[...]
# ---------------------------------------------------------------------------

class TestTabsAPI:
    """Verify that ft.Tabs uses the Flet 0.84.0 constructor signature."""

    def test_tabs_rejects_tabs_keyword(self):
        """ft.Tabs(tabs=[...]) must raise TypeError in Flet ≥ 0.84.0."""
        with pytest.raises(TypeError, match="tabs"):
            ft.Tabs(tabs=[ft.Tab("A")])

    def test_tabs_accepts_content_and_length(self):
        tabs = ft.Tabs(
            content=ft.Column(
                [
                    ft.TabBar(tabs=[ft.Tab("A"), ft.Tab("B")]),
                    ft.TabBarView(controls=[ft.Container(), ft.Container()]),
                ]
            ),
            length=2,
        )
        assert tabs.length == 2


# ---------------------------------------------------------------------------
# 3.  Every function that calls ft.use_state must be @ft.component
# ---------------------------------------------------------------------------

class TestComponentDecoratorPresence:
    """AST-based check: any function using ft.use_state must be decorated
    with @ft.component, otherwise it will crash at runtime with
    'RuntimeError: No current renderer is set.'
    """

    @staticmethod
    def _collect_violations() -> list[str]:
        """Walk all .py files under src/ and find functions that call
        ft.use_state (or just use_state) but lack @ft.component.
        """
        violations: list[str] = []

        for py_file in SRC_DIR.rglob("*.py"):
            source = py_file.read_text()
            try:
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                # Check whether the function body contains a call to
                # ft.use_state or use_state
                uses_state = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func = child.func
                        # ft.use_state(...)
                        if (
                            isinstance(func, ast.Attribute)
                            and func.attr == "use_state"
                        ):
                            uses_state = True
                            break
                        # use_state(...)  (if imported directly)
                        if isinstance(func, ast.Name) and func.id == "use_state":
                            uses_state = True
                            break

                if not uses_state:
                    continue

                # Now verify @ft.component is present
                has_decorator = False
                for dec in node.decorator_list:
                    # @ft.component
                    if (
                        isinstance(dec, ast.Attribute)
                        and isinstance(dec.value, ast.Name)
                        and dec.value.id == "ft"
                        and dec.attr == "component"
                    ):
                        has_decorator = True
                        break
                    # @component  (if imported directly)
                    if isinstance(dec, ast.Name) and dec.id == "component":
                        has_decorator = True
                        break

                if not has_decorator:
                    rel = py_file.relative_to(SRC_DIR)
                    violations.append(
                        f"{rel}:{node.lineno} — function '{node.name}' calls "
                        f"ft.use_state() but is not decorated with @ft.component"
                    )

        return violations

    def test_no_use_state_without_component_decorator(self):
        violations = self._collect_violations()
        assert violations == [], (
            "Functions using ft.use_state() without @ft.component will crash "
            "at runtime with 'No current renderer is set':\n"
            + "\n".join(f"  • {v}" for v in violations)
        )


# ---------------------------------------------------------------------------
# 4.  Source-level guard: target.py must not use deprecated Flet patterns
# ---------------------------------------------------------------------------

class TestTargetDetailsSource:
    """Scan target.py source for known-bad patterns that caused past crashes."""

    @pytest.fixture()
    def target_source(self) -> str:
        return (SRC_DIR / "components" / "targets" / "target.py").read_text()

    def test_no_tab_text_keyword(self, target_source: str):
        """Ensure no ft.Tab(text=...) calls remain."""
        tree = ast.parse(target_source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_tab_call = (
                isinstance(func, ast.Attribute)
                and func.attr == "Tab"
            )
            if not is_tab_call:
                continue
            for kw in node.keywords:
                assert kw.arg != "text", (
                    f"Line {node.lineno}: ft.Tab(text=...) is invalid in "
                    f"Flet 0.84.0. Use ft.Tab(label=...) or positional arg."
                )

    def test_no_tabs_tabs_keyword(self, target_source: str):
        """Ensure no ft.Tabs(tabs=[...]) calls remain."""
        tree = ast.parse(target_source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_tabs_call = (
                isinstance(func, ast.Attribute)
                and func.attr == "Tabs"
            )
            if not is_tabs_call:
                continue
            for kw in node.keywords:
                assert kw.arg != "tabs", (
                    f"Line {node.lineno}: ft.Tabs(tabs=[...]) is invalid in "
                    f"Flet 0.84.0. Use ft.Tabs(content=..., length=...)."
                )

    def test_no_tab_content_keyword(self, target_source: str):
        """Ensure no ft.Tab(content=...) calls remain."""
        tree = ast.parse(target_source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_tab_call = (
                isinstance(func, ast.Attribute)
                and func.attr == "Tab"
            )
            if not is_tab_call:
                continue
            for kw in node.keywords:
                assert kw.arg != "content", (
                    f"Line {node.lineno}: ft.Tab(content=...) is invalid in "
                    f"Flet 0.84.0. Use ft.TabBarView(controls=[...]) instead."
                )


# ---------------------------------------------------------------------------
# 5.  @ft.component must never be called from an on_click/event handler
# ---------------------------------------------------------------------------

class TestNoComponentCallsFromEventHandlers:
    """AST-based check: functions called from inside event handlers (on_click,
    on_change, on_submit, etc.) must NOT be @ft.component-decorated, because
    event handlers run outside the Flet renderer context.

    This catches the recurring 'RuntimeError: No current renderer is set'
    crash that has been re-introduced multiple times (PRs #10-#14).
    """

    @staticmethod
    def _collect_component_names() -> set[str]:
        """Return names of all @ft.component-decorated functions under src/."""
        names: set[str] = set()
        for py_file in SRC_DIR.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(), filename=str(py_file))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for dec in node.decorator_list:
                    if (
                        isinstance(dec, ast.Attribute)
                        and isinstance(dec.value, ast.Name)
                        and dec.value.id == "ft"
                        and dec.attr == "component"
                    ):
                        names.add(node.name)
                    elif isinstance(dec, ast.Name) and dec.id == "component":
                        names.add(node.name)
        return names

    @staticmethod
    def _find_event_handler_bodies(tree: ast.AST) -> list[tuple[str, ast.FunctionDef]]:
        """Find inner functions assigned to event-handler keyword args
        (on_click, on_change, on_submit, etc.) and return (handler_name, node).
        Also detect functions whose name starts with common event-handler
        patterns that are referenced by on_click= etc.
        """
        # Collect function names that are assigned to on_* keyword args
        handler_names: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg and kw.arg.startswith("on_") and isinstance(kw.value, ast.Name):
                    handler_names.add(kw.value.id)

        # Return FunctionDef nodes that match those names
        handlers: list[tuple[str, ast.FunctionDef]] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in handler_names:
                    handlers.append((node.name, node))
        return handlers

    def test_no_component_calls_in_event_handlers(self):
        """Verify no @ft.component function is called from event handlers."""
        component_names = self._collect_component_names()
        if not component_names:
            return  # nothing to check

        violations: list[str] = []

        for py_file in SRC_DIR.rglob("*.py"):
            try:
                source = py_file.read_text()
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            handlers = self._find_event_handler_bodies(tree)
            for handler_name, handler_node in handlers:
                for child in ast.walk(handler_node):
                    if not isinstance(child, ast.Call):
                        continue
                    called_name = None
                    if isinstance(child.func, ast.Name):
                        called_name = child.func.id
                    elif isinstance(child.func, ast.Attribute):
                        called_name = child.func.attr
                    if called_name and called_name in component_names:
                        rel = py_file.relative_to(SRC_DIR)
                        violations.append(
                            f"{rel}:{child.lineno} — event handler "
                            f"'{handler_name}' calls @ft.component "
                            f"'{called_name}'. Components cannot be "
                            f"instantiated from event handlers (no renderer "
                            f"context)."
                        )

        assert violations == [], (
            "@ft.component functions called from event handlers will crash "
            "with 'RuntimeError: No current renderer is set':\n"
            + "\n".join(f"  • {v}" for v in violations)
        )

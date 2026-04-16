"""C2 session management view."""
import asyncio
import threading

import flet as ft
from models.apt import Apt
from components.c2.session_table import SessionTable
from components.c2.agent_detail import AgentDetail

CYAN = ft.Colors.CYAN_400


@ft.component
def C2View(state: Apt):
    selected_session_id, set_selected_session_id = ft.use_state("")
    tick, set_tick = ft.use_state(0)
    refresh_state, _ = ft.use_state(lambda: {"stop": threading.Event(), "started": False, "tick": 0})

    def on_select(session_id: str):
        set_selected_session_id(session_id)

    def kill_all_local_beacons(_: ft.ControlEvent):
        stopped = state.kill_all_local_beacons()
        set_selected_session_id("")
        message = f"Stopped {stopped} local beacon(s)."
        page = ft.context.page
        page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Kill All Complete"),
                content=ft.Text(message),
                actions=[
                    ft.TextButton("OK", on_click=lambda _: page.pop_dialog()),
                ],
            )
        )

    async def _refresh_loop():
        while not refresh_state["stop"].is_set():
            await asyncio.sleep(1)
            refresh_state["tick"] += 1
            set_tick(refresh_state["tick"])
            state.trigger_update()

    def _stop_refresh():
        refresh_state["stop"].set()

    if not refresh_state["started"]:
        refresh_state["started"] = True
        ft.context.page.run_task(_refresh_loop)

    ft.on_unmounted(_stop_refresh)

    page_width = getattr(ft.context.page.window, "width", 0) or 0
    is_compact_layout = page_width > 0 and page_width < 1350

    agents_panel = ft.Container(
        ft.Column(
            [
                ft.Text(
                    "Active Agents",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_300,
                ),
                SessionTable(state=state, on_select=on_select, tick=tick),
            ],
            spacing=8,
            expand=True,
        ),
        expand=True,
    )

    detail_panel = ft.Container(
        AgentDetail(state=state, session_id=selected_session_id),
        width=None if is_compact_layout else 420,
        expand=is_compact_layout,
        height=340 if is_compact_layout else None,
    )

    content_panel: ft.Control
    if is_compact_layout:
        content_panel = ft.Column(
            [
                agents_panel,
                detail_panel,
            ],
            expand=True,
            spacing=12,
        )
    else:
        content_panel = ft.Row(
            [
                agents_panel,
                detail_panel,
            ],
            expand=True,
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    return ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.WIFI_TETHERING, color=CYAN, size=22),
                        ft.Text(
                            "C2 Sessions",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=CYAN,
                            expand=True,
                        ),
                        ft.FilledButton(
                            "Kill All (Local) Beacons",
                            icon=ft.Icons.CANCEL,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.RED_700,
                                color=ft.Colors.WHITE,
                            ),
                            on_click=kill_all_local_beacons,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=1, bgcolor=ft.Colors.GREY_800),
                content_panel,
            ],
            spacing=12,
            expand=True,
        ),
        expand=True,
        padding=24,
    )

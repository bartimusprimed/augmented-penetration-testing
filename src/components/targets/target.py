import flet as ft
import logging
import time
from typing import Callable, cast
from dataclasses import dataclass, field
from ipaddress import IPv4Address
from models.target import Target
from models.apt import Apt
from components.targets.add import add_target

CYAN = ft.Colors.CYAN_400


def _fmt_last_seen(ts: float) -> str:
    if ts == 0.0:
        return "never"
    delta = int(time.time() - ts)
    if delta < 60:
        return f"{delta}s ago"
    if delta < 3600:
        return f"{delta // 60}m ago"
    return f"{delta // 3600}h ago"


def _overview_tab(t: Target):
    """Activity log list."""
    entries = [ft.Text(entry, selectable=True) for entry in t.activity_log]
    return ft.Container(
        ft.ListView(entries, expand=True, spacing=2),
        expand=True,
        padding=ft.Padding(left=4, right=4, top=8, bottom=8),
    )


def _shell_tab(t: Target, state: Apt):
    """Emulated shell: send commands to beacon, view output history."""
    cmd_text, set_cmd_text = ft.use_state("")

    def send_command(e):
        cmd = cmd_text.strip()
        if not cmd or not t.beacon_session_id:
            return
        # Use the beacon module's public push_command method
        beacon_mod = state.modules.classes.get("beacon")
        if beacon_mod and beacon_mod.push_command(t.beacon_session_id, cmd):
            t.beacon_shell_history.append(f"$ {cmd}")
            cast(ft.Observable, t).notify()
        set_cmd_text("")

    history_items = [
        ft.Text(entry, selectable=True, font_family="monospace", size=12,
                color=ft.Colors.GREEN_300 if entry.startswith("$ ") else ft.Colors.GREY_300)
        for entry in t.beacon_shell_history
    ]

    not_connected_msg = (
        ft.Container(
            ft.Column(
                [
                    ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.GREY_700, size=40),
                    ft.Text("No active beacon session", color=ft.Colors.GREY_500, size=13),
                    ft.Text(
                        "Run the 'C2 Beacon' module to start a beacon on this target.",
                        color=ft.Colors.GREY_700,
                        size=11,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=24,
        )
        if not t.beacon_connected
        else ft.Container()
    )

    return ft.Column(
        [
            not_connected_msg,
            ft.Container(
                ft.ListView(history_items, expand=True, spacing=2),
                expand=True,
                bgcolor=ft.Colors.GREY_900,
                border_radius=8,
                padding=8,
            ),
            ft.Row(
                [
                    ft.TextField(
                        value=cmd_text,
                        hint_text="Enter shell command…",
                        expand=True,
                        dense=True,
                        on_change=lambda e: set_cmd_text(e.control.value),
                        on_submit=send_command,
                        border_color=CYAN,
                        focused_border_color=CYAN,
                        disabled=not t.beacon_connected,
                    ),
                    ft.IconButton(
                        ft.Icons.SEND,
                        icon_color=CYAN,
                        on_click=send_command,
                        disabled=not t.beacon_connected,
                        tooltip="Send command",
                    ),
                ],
                spacing=8,
            ),
        ],
        expand=True,
        spacing=8,
    )


def _beacon_tab(t: Target):
    """Beacon status and configuration."""
    status_color = ft.Colors.GREEN_400 if t.beacon_connected else ft.Colors.GREY_600
    status_label = "Connected" if t.beacon_connected else "Not connected"

    def on_interval_change(e: ft.Event[ft.TextField]):
        try:
            val = int(e.control.value)
            if val > 0:
                t.update_field("beacon_interval", val)
        except ValueError:
            pass

    def on_port_change(e: ft.Event[ft.TextField]):
        try:
            val = int(e.control.value)
            if 1 <= val <= 65535:
                t.update_field("beacon_c2_port", val)
        except ValueError:
            pass

    return ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CIRCLE, color=status_color, size=14),
                        ft.Text(status_label, size=13, color=status_color),
                    ],
                    spacing=6,
                ),
                ft.Divider(color=ft.Colors.GREY_800),
                ft.Text("Session ID", size=11, color=ft.Colors.GREY_500),
                ft.Text(t.beacon_session_id or "—", selectable=True, size=12),
                ft.Text("Last check-in", size=11, color=ft.Colors.GREY_500),
                ft.Text(_fmt_last_seen(t.beacon_last_seen), size=12),
                ft.Divider(color=ft.Colors.GREY_800),
                ft.Text("C2 port", size=11, color=ft.Colors.GREY_500),
                ft.TextField(
                    value=str(t.beacon_c2_port),
                    on_blur=on_port_change,
                    dense=True,
                    width=120,
                    keyboard_type=ft.KeyboardType.NUMBER,
                ),
                ft.Text("Check-in interval (seconds)", size=11, color=ft.Colors.GREY_500),
                ft.TextField(
                    value=str(t.beacon_interval),
                    on_blur=on_interval_change,
                    dense=True,
                    width=120,
                    keyboard_type=ft.KeyboardType.NUMBER,
                ),
            ],
            spacing=6,
        ),
        padding=ft.Padding(left=4, right=4, top=8, bottom=8),
        expand=True,
    )


@ft.component
def target(t: Target, state: Apt):
    def show_target_details(e: ft.Event[ft.Button]):
        selected_target = state.get_target(target_ip.value)

        content = ft.Container(
            ft.Tabs(
                tabs=[
                    ft.Tab(
                        text="Overview",
                        icon=ft.Icons.LIST_ALT_OUTLINED,
                        content=_overview_tab(t=selected_target),
                    ),
                    ft.Tab(
                        text="Shell",
                        icon=ft.Icons.TERMINAL,
                        content=_shell_tab(t=selected_target, state=state),
                    ),
                    ft.Tab(
                        text="Beacon",
                        icon=ft.Icons.WIFI_TETHERING,
                        content=_beacon_tab(t=selected_target),
                    ),
                ],
                expand=True,
            ),
            expand=True,
            height=420,
            width=520,
        )

        ft.context.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(f"Target: {t.ip_label}"),
                alignment=ft.Alignment.CENTER,
                icon=ft.Icon(ft.Icons.INFO_OUTLINED),
                content=content,
                actions=[
                    ft.TextButton(
                        "Delete Target",
                        on_click=lambda e: state.remove_target(selected_target),
                        style=ft.ButtonStyle(color=ft.Colors.RED_400),
                    ),
                    ft.TextButton("Close", on_click=lambda _: ft.context.page.pop_dialog()),
                ],
            )
        )

    def update_target_field_and_notify(e: ft.Event[ft.Checkbox]):
        t.update_field("is_selected", e.control.value)
        state.trigger_update()

    target_ip = ft.Text(t.ip_label, weight=ft.FontWeight.BOLD, size=24)
    target_status = ft.Text(
        t.current_status,
        no_wrap=False,
        max_lines=3,
        overflow=ft.TextOverflow.ELLIPSIS,
        text_align=ft.TextAlign.CENTER,
        size=12,
    )

    beacon_indicator = (
        ft.Icon(ft.Icons.WIFI_TETHERING, color=ft.Colors.GREEN_400, size=14, tooltip="Beacon connected")
        if t.beacon_connected
        else ft.Container()
    )

    return ft.Container(
        ft.Card(
            ft.Container(
                ft.Column(
                    [
                        ft.Row(
                            [ft.Checkbox("Selected", t.is_selected, on_change=update_target_field_and_notify, label_position=ft.LabelPosition.RIGHT)],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Row([target_ip, beacon_indicator], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
                        ft.Column(
                            [
                                ft.Text("Status:", size=12, weight=ft.FontWeight.BOLD),
                                target_status,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2,
                        ),
                        ft.Button("Target Details", data=t.ip_label,
                                  on_click=show_target_details, elevation=5, bgcolor=ft.Colors.BLUE_GREY)
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=8,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ), elevation=3, bgcolor=t.color_status
        ), alignment=ft.Alignment.CENTER, expand=True
    )

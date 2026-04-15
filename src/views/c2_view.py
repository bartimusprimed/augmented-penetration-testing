"""C2 session management view."""
import flet as ft
from models.apt import Apt
from components.c2.session_table import SessionTable
from components.c2.agent_detail import AgentDetail

CYAN = ft.Colors.CYAN_400


@ft.component
def C2View(state: Apt):
    selected_session_id, set_selected_session_id = ft.use_state("")

    def on_select(session_id: str):
        set_selected_session_id(session_id)

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
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=1, bgcolor=ft.Colors.GREY_800),
                ft.Row(
                    [
                        ft.Container(
                            ft.Column(
                                [
                                    ft.Text(
                                        "Active Agents",
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.GREY_300,
                                    ),
                                    SessionTable(state=state, on_select=on_select),
                                ],
                                spacing=8,
                                expand=True,
                            ),
                            expand=True,
                        ),
                        ft.Container(
                            AgentDetail(state=state, session_id=selected_session_id),
                            width=420,
                        ),
                    ],
                    expand=True,
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=12,
            expand=True,
        ),
        expand=True,
        padding=24,
    )

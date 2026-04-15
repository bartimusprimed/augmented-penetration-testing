from typing import Callable
import flet as ft

CYAN = ft.Colors.CYAN_400
NAV_BG = "#0a141c"


def NavBar(current_page: int, function_to_call: Callable) -> ft.Container:
    nav_items = [
        (ft.Icons.HOME_OUTLINED, "Home", 0),
        (ft.Icons.COMPUTER_OUTLINED, "Targets", 1),
        (ft.Icons.VIEW_MODULE_OUTLINED, "Modules", 2),
        (ft.Icons.LINK_OUTLINED, "Chains", 3),
        (ft.Icons.WIFI_TETHERING, "C2", 4),
        (ft.Icons.SETTINGS_APPLICATIONS_OUTLINED, "Settings", 5),
    ]

    def _nav_button(icon, label, index):
        selected = current_page == index
        return ft.IconButton(
            icon=icon,
            icon_color=CYAN if selected else ft.Colors.GREY_500,
            icon_size=26,
            tooltip=label,
            on_click=lambda _, i=index: function_to_call(i),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.CYAN_900 if selected else ft.Colors.TRANSPARENT,
                },
            ),
        )

    logo = ft.Container(
        ft.Image(src="icon.png", width=36, height=36, fit=ft.BoxFit.CONTAIN),
        margin=ft.Margin(bottom=16, top=8, left=0, right=0),
    )

    buttons = [_nav_button(icon, label, idx) for icon, label, idx in nav_items]

    return ft.Container(
        ft.Column(
            [logo, *buttons],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        width=60,
        bgcolor=NAV_BG,
        padding=ft.Padding(left=6, right=6, top=8, bottom=8),
        border=ft.Border(right=ft.BorderSide(1, ft.Colors.GREY_800)),
    )

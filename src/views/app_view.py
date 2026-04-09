import flet as ft
from views.home_view import Home
from views.targets_view import Targets
from views.settings_view import Settings
from views.modules_view import Modules
from views.chains_view import Chains
from components.app.navbar import NavBar
from models.apt import Apt
from utils.permissions import check_raw_packet_access

APP_BG = "#0d1b24"


@ft.component
def App():
    apt_state, _ = ft.use_state(lambda: Apt())
    current_page, set_current_page = ft.use_state(0)

    def _show_startup_warning():
        warning = check_raw_packet_access()
        if warning:
            ft.context.page.show_dialog(ft.AlertDialog(
                icon=ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER_400, size=40),
                title=ft.Text("Privilege Setup Required"),
                content=ft.Text(warning, selectable=True),
                actions=[
                    ft.TextButton("OK", on_click=lambda _: ft.context.page.pop_dialog()),
                ],
            ))

    ft.on_mounted(_show_startup_warning)

    def goto_page(page_index):
        set_current_page(page_index)

    match current_page:
        case 0:
            content = Home(apt_state)
        case 1:
            content = Targets(apt_state)
        case 2:
            content = Modules(apt_state)
        case 3:
            content = Chains(apt_state)
        case 4:
            content = Settings(apt_state)
        case _:
            content = Home(apt_state)

    return ft.Container(
        ft.Row(
            [
                NavBar(current_page, goto_page),
                ft.Container(content, expand=True),
            ],
            spacing=0,
            expand=True,
        ),
        bgcolor=APP_BG,
        expand=True,
    )

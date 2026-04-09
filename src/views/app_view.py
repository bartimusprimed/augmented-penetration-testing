import flet as ft
from views.home_view import Home
from views.targets_view import Targets
from views.settings_view import Settings
from views.modules_view import Modules
from components.app.navbar import NavBar
from models.apt import Apt


@ft.component
def App():
    apt_state, _ = ft.use_state(lambda: Apt())
    current_page, set_current_page = ft.use_state(0)

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
            content = Settings(apt_state)
        case _:
            content = Home(apt_state)

    return ft.Pagelet(
        content=ft.Column([content], expand=True),
        navigation_bar=NavBar(goto_page),
        expand=True,
    )

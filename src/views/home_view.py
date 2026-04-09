import flet as ft

from models.apt import Apt
from components.home.hero import Hero
from components.home.workflow import Workflow

CYAN = ft.Colors.CYAN_400


@ft.component
def Home(state: Apt):
    return ft.Container(
        ft.Column(
            [
                Hero(state),
                ft.Divider(color=ft.Colors.GREY_800, height=1),
                Workflow(),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=24,
        ),
        expand=True,
        padding=40,
    )

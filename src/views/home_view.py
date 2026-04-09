import flet as ft

from models.apt import Apt
from components.home.hero import Hero
from components.home.workflow import Workflow


@ft.component
def Home(state: Apt):
    return ft.Container(
        ft.Column([
            Hero(state),
            Workflow()
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), expand=True, padding=50
    )

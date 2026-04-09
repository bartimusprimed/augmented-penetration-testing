import flet as ft

from models.apt import Apt


@ft.component
def Hero(state: Apt):
    return ft.Container(
        ft.Column([
            ft.Text(state.title, size=50),
            ft.Text(state.description, size=20),
            ft.Image("icon.png", scale=0.2, margin=-100),
            ft.Text(f"Version: {state.version}"),
        ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ), alignment=ft.Alignment.TOP_CENTER
    )

import flet as ft

from models.apt import Apt

CYAN = ft.Colors.CYAN_400


@ft.component
def Hero(state: Apt):
    return ft.Container(
        ft.Column(
            [
                ft.Image(
                    src="icon.png",
                    width=220,
                    height=220,
                    fit=ft.BoxFit.CONTAIN,
                    border_radius=24,
                ),
                ft.Text(
                    state.title,
                    size=48,
                    weight=ft.FontWeight.BOLD,
                    color=CYAN,
                ),
                ft.Text(
                    state.description,
                    size=16,
                    color=ft.Colors.GREY_400,
                    italic=True,
                ),
                ft.Text(
                    f"Version: {state.version}",
                    size=12,
                    color=ft.Colors.GREY_600,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        alignment=ft.Alignment.TOP_CENTER,
    )

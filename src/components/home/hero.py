import flet as ft

from models.apt import Apt


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
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        alignment=ft.Alignment.TOP_CENTER,
    )

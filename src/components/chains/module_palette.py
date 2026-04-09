import flet as ft
from models.apt import Apt
from modules.base_module import APT_MODULE

CYAN = ft.Colors.CYAN_400


def _draggable_module(key: str, mod: APT_MODULE) -> ft.Control:
    name = mod.name if mod.name else key

    return ft.Draggable(
        group="chain_node",
        data=key,
        content=ft.Container(
            ft.Row(
                [
                    ft.Icon(ft.Icons.DRAG_INDICATOR, size=16, color=ft.Colors.GREY_600),
                    ft.Text(name, size=13, color=ft.Colors.WHITE, expand=True, no_wrap=True),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.GREY_800,
            border_radius=6,
            padding=ft.Padding(left=8, right=8, top=8, bottom=8),
            border=ft.Border.all(1, ft.Colors.GREY_700),
            ink=True,
        ),
        content_when_dragging=ft.Container(
            ft.Text(name, size=13, color=CYAN),
            bgcolor="#0d3050",
            border_radius=6,
            padding=8,
            opacity=0.7,
            border=ft.Border.all(1, CYAN),
        ),
    )


@ft.component
def ModulePalette(state: Apt):
    all_modules = state.modules.classes

    items: list[ft.Control] = [
        ft.Text("Available Modules", size=13, weight=ft.FontWeight.BOLD, color=CYAN),
        ft.Text("Drag into chain →", size=11, color=ft.Colors.GREY_500),
        ft.Container(height=1, bgcolor=ft.Colors.GREY_800),
    ]
    for key, mod in all_modules.items():
        items.append(_draggable_module(key, mod))

    return ft.Container(
        ft.Column(items, spacing=6, scroll=ft.ScrollMode.AUTO, expand=True),
        width=200,
        bgcolor=ft.Colors.GREY_900,
        border_radius=12,
        padding=12,
        border=ft.Border(right=ft.BorderSide(1, ft.Colors.GREY_800)),
    )

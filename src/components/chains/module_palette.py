import flet as ft
from models.apt import Apt
from models.module_metadata import AttackTactic
from modules.base_module import APT_MODULE
from components.modules.module_card import TACTIC_COLORS

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
    active_tactic, set_active_tactic = ft.use_state(None)

    all_modules = state.modules.classes
    tactics_in_use: list[AttackTactic] = state.modules.get_tactics_in_use()

    # Filter modules by selected tactic
    if active_tactic is None:
        visible = all_modules
    else:
        visible = {k: v for k, v in all_modules.items() if v.tactic == active_tactic}

    # Build tactic filter chips
    chip_items: list[ft.Control] = [
        ft.Chip(
            label="All",
            selected=active_tactic is None,
            selected_color=ft.Colors.BLUE_700,
            on_click=lambda _: set_active_tactic(None),
        )
    ]
    for tactic in tactics_in_use:
        color = TACTIC_COLORS.get(tactic, ft.Colors.GREY_700)
        chip_items.append(
            ft.Chip(
                label=tactic.display_name,
                selected=active_tactic == tactic,
                selected_color=color,
                on_click=lambda _, t=tactic: set_active_tactic(t),
            )
        )

    module_items: list[ft.Control] = []
    for key, mod in visible.items():
        module_items.append(_draggable_module(key, mod))

    items: list[ft.Control] = [
        ft.Text("Available Modules", size=13, weight=ft.FontWeight.BOLD, color=CYAN),
        ft.Text("Drag into chain →", size=11, color=ft.Colors.GREY_500),
        ft.Container(
            ft.Row(chip_items, wrap=True, spacing=4, run_spacing=4),
            padding=ft.Padding(left=0, right=0, top=4, bottom=4),
        ),
        ft.Container(height=1, bgcolor=ft.Colors.GREY_800),
        *module_items,
    ]

    return ft.Container(
        ft.Column(items, spacing=6, scroll=ft.ScrollMode.AUTO, expand=True),
        width=200,
        bgcolor=ft.Colors.GREY_900,
        border_radius=12,
        padding=12,
        border=ft.Border(right=ft.BorderSide(1, ft.Colors.GREY_800)),
    )

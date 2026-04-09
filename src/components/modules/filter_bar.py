from typing import Callable
import flet as ft
from models.module_metadata import AttackTactic, TargetOS, TargetArch
from components.modules.module_card import TACTIC_COLORS


@ft.component
def FilterBar(
    tactics_in_use: list[AttackTactic],
    active_tactic: AttackTactic | None,
    os_filter: TargetOS | None,
    arch_filter: TargetArch | None,
    on_tactic_change: Callable[[AttackTactic | None], None],
    on_os_change: Callable[[TargetOS | None], None],
    on_arch_change: Callable[[TargetArch | None], None],
):
    tactic_chips: list[ft.Control] = [
        ft.Chip(
            label="All",
            selected=active_tactic is None,
            selected_color=ft.Colors.BLUE_700,
            on_click=lambda _: on_tactic_change(None),
        )
    ]
    for tactic in tactics_in_use:
        color = TACTIC_COLORS.get(tactic, ft.Colors.GREY_700)
        tactic_chips.append(
            ft.Chip(
                label=tactic.display_name,
                selected=active_tactic == tactic,
                selected_color=color,
                on_click=lambda _, t=tactic: on_tactic_change(t),
            )
        )

    os_options = [ft.dropdown.Option(key="any", text="All OS")] + [
        ft.dropdown.Option(key=os_val.name, text=os_val.value)
        for os_val in TargetOS
        if os_val != TargetOS.ANY
    ]
    arch_options = [ft.dropdown.Option(key="any", text="All Arch")] + [
        ft.dropdown.Option(key=arch_val.name, text=arch_val.value)
        for arch_val in TargetArch
        if arch_val != TargetArch.ANY
    ]

    def handle_os_change(e: ft.Event[ft.Dropdown]):
        if e.control.value == "any":
            on_os_change(None)
        else:
            on_os_change(TargetOS[e.control.value])

    def handle_arch_change(e: ft.Event[ft.Dropdown]):
        if e.control.value == "any":
            on_arch_change(None)
        else:
            on_arch_change(TargetArch[e.control.value])

    return ft.Container(
        ft.Column(
            [
                ft.Row(tactic_chips, wrap=True, spacing=6, run_spacing=4),
                ft.Row(
                    [
                        ft.Dropdown(
                            options=os_options,
                            value=os_filter.name if os_filter else "any",
                            on_select=handle_os_change,
                            width=140,
                            dense=True,
                        ),
                        ft.Dropdown(
                            options=arch_options,
                            value=arch_filter.name if arch_filter else "any",
                            on_select=handle_arch_change,
                            width=140,
                            dense=True,
                        ),
                    ],
                    spacing=10,
                ),
            ],
            spacing=8,
        ),
        padding=ft.Padding(left=12, right=12, top=10, bottom=10),
        bgcolor=ft.Colors.GREY_900,
        border_radius=10,
        margin=ft.Margin(left=0, right=0, top=0, bottom=8),
    )

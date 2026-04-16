import flet as ft
from models.apt import Apt
from components.targets.target import target
from components.targets.context import TargetContextActions


@ft.component
def target_list(state: Apt):
    targets = [target(t, state) for t in state.targets]
    selected_target_count = len(state.get_selected_targets())

    header = ft.Container(
        ft.Row(
            [
                ft.Text("Selection", size=11, color=ft.Colors.GREY_500, width=120),
                ft.Text("Target", size=11, color=ft.Colors.GREY_500, width=170),
                ft.Text("Status", size=11, color=ft.Colors.GREY_500, expand=True),
                ft.Text("Actions", size=11, color=ft.Colors.GREY_500, width=140),
            ],
            spacing=12,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(left=12, right=12, top=6, bottom=6),
        bgcolor=ft.Colors.GREY_800,
        border_radius=ft.BorderRadius(top_left=8, top_right=8, bottom_left=0, bottom_right=0),
    )

    rows = [
        ft.Container(r, margin=ft.Margin(bottom=6, top=0, left=0, right=0))
        for r in targets
    ]

    target_table = ft.Container(
        ft.Column(
            [header, ft.Column(rows, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)],
            spacing=0,
            expand=True,
        ),
        border=ft.Border.all(1, ft.Colors.GREY_800),
        border_radius=8,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        expand=True,
    )

    if selected_target_count < 1:
        return ft.Container(
            ft.Column([
                target_table
            ], alignment=ft.MainAxisAlignment.START, expand=True, scroll=ft.ScrollMode.ALWAYS
            ), expand=True)
    else:
        return ft.Container(
            ft.Column([
                TargetContextActions(state, selected_target_count),
                target_table
            ], alignment=ft.MainAxisAlignment.START, expand=True, scroll=ft.ScrollMode.ALWAYS
            ), expand=True)

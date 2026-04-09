import flet as ft
from models.apt import Apt
from components.targets.list import target_list
from components.targets.add import add_target


@ft.component
def Targets(state: Apt):
    return ft.Container(
        ft.Column([
            ft.Row([
                ft.Button("Toggle All Targets",
                          on_click=state.select_all_targets),
                add_target(state),
            ]),
            ft.Column([
                target_list(state)
            ], expand=True)
        ], expand=True), expand=True
    )

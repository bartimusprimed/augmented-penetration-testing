import flet as ft
from components.targets.actions import TargetActions
from models.apt import Apt


@ft.component
def TargetContextActions(state: Apt, count: int):
    return ft.Column(
        [
            ft.Text(f"Targets selected: {count}"),
            TargetActions(state),
        ],
        spacing=6,
    )

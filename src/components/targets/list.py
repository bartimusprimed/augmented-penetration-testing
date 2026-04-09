import flet as ft
import logging
from typing import Callable
from dataclasses import dataclass, field
from ipaddress import IPv4Address
from models.apt import Apt
from components.targets.target import target
from components.targets.context import TargetContextActions


@ft.component
def target_list(state: Apt):
    targets = [target(t, state) for t in state.targets]
    selected_target_count = len(state.get_selected_targets())
    if selected_target_count < 1:
        return ft.Container(
            ft.Column([
                ft.GridView([*targets], runs_count=6,
                            expand=False, max_extent=250)
            ], alignment=ft.MainAxisAlignment.START, expand=True, scroll=ft.ScrollMode.ALWAYS
            ), expand=True)
    else:
        return ft.Container(
            ft.Column([
                TargetContextActions(state, selected_target_count),
                ft.GridView([*targets], runs_count=6,
                            expand=False, max_extent=250)
            ], alignment=ft.MainAxisAlignment.START, expand=True, scroll=ft.ScrollMode.ALWAYS
            ), expand=True)

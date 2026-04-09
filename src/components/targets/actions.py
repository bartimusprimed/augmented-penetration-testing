import flet as ft
from models.apt import Apt


@ft.component
def TargetActions(state: Apt):
    action_buttons = []
    for k in state.get_enabled_modules():
        mod = state.modules.classes[k]
        display_name = mod.name or k
        action_buttons.append(
            ft.Button(display_name, data=k, on_click=state.run_action, bgcolor=ft.Colors.GREY_800, disabled=mod.is_running))
    return ft.Row(action_buttons)

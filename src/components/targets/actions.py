import flet as ft
from models.apt import Apt


@ft.component
def TargetActions(state: Apt):
    module_buttons: list[ft.Control] = []
    for k in state.get_enabled_modules():
        mod = state.modules.classes[k]
        display_name = mod.name or k
        module_buttons.append(
            ft.Button(
                display_name,
                data=k,
                on_click=state.run_action,
                bgcolor=ft.Colors.GREY_800,
                disabled=mod.is_running,
            )
        )

    async def run_chain_from_targets(e: ft.Event[ft.Button]):
        chain_idx = int(e.control.data)
        if 0 <= chain_idx < len(state.chains):
            await state.run_chain(state.chains[chain_idx], e)

    chain_buttons: list[ft.Control] = []
    for idx, chain in enumerate(state.chains):
        chain_buttons.append(
            ft.Button(
                chain.name,
                data=str(idx),
                icon=ft.Icons.LINK,
                on_click=run_chain_from_targets,
                bgcolor=ft.Colors.BLUE_GREY_700,
                disabled=chain.is_running,
            )
        )

    return ft.Column(
        [
            ft.Text("Modules", size=12, color=ft.Colors.GREY_400),
            ft.Row(module_buttons, wrap=True, spacing=8, run_spacing=8),
            ft.Text("Chains", size=12, color=ft.Colors.GREY_400),
            ft.Row(
                chain_buttons
                if chain_buttons
                else [ft.Text("No chains created yet", size=12, color=ft.Colors.GREY_600)],
                wrap=True,
                spacing=8,
                run_spacing=8,
            ),
        ],
        spacing=6,
    )

import flet as ft
from models.apt import Apt
from models.module_metadata import AttackTactic, TargetOS, TargetArch
from components.modules.filter_bar import FilterBar
from components.modules.tactic_section import TacticSection


@ft.component
def Modules(state: Apt):
    active_tactic, set_active_tactic = ft.use_state(None)
    os_filter, set_os_filter = ft.use_state(None)
    arch_filter, set_arch_filter = ft.use_state(None)

    tactics_in_use = state.modules.get_tactics_in_use()
    filtered = state.modules.get_modules_filtered(
        tactic=active_tactic,
        os_filter=os_filter,
        arch_filter=arch_filter,
    )

    # Group filtered modules by tactic, preserving attack-chain order
    sections: list[ft.Control] = []
    for tactic in tactics_in_use:
        if active_tactic is not None and tactic != active_tactic:
            continue
        tactic_modules = {k: v for k, v in filtered.items() if v.tactic == tactic}
        if tactic_modules:
            sections.append(TacticSection(tactic=tactic, modules=tactic_modules))

    return ft.Container(
        ft.Column(
            [
                ft.Text("Modules", weight=ft.FontWeight.BOLD, size=22),
                FilterBar(
                    tactics_in_use=tactics_in_use,
                    active_tactic=active_tactic,
                    os_filter=os_filter,
                    arch_filter=arch_filter,
                    on_tactic_change=set_active_tactic,
                    on_os_change=set_os_filter,
                    on_arch_change=set_arch_filter,
                ),
                ft.ListView(sections, expand=True, spacing=4),
            ],
            expand=True,
        ),
        padding=16,
        expand=True,
    )

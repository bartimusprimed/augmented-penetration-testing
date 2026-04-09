import flet as ft
from modules.base_module import APT_MODULE
from models.module_metadata import AttackTactic, TargetOS, TargetArch

# Tactic → accent colour mapping (used for the tactic badge on each card)
TACTIC_COLORS: dict[AttackTactic, ft.Colors] = {
    AttackTactic.RECONNAISSANCE: ft.Colors.BLUE_700,
    AttackTactic.RESOURCE_DEVELOPMENT: ft.Colors.INDIGO_700,
    AttackTactic.INITIAL_ACCESS: ft.Colors.ORANGE_700,
    AttackTactic.EXECUTION: ft.Colors.RED_700,
    AttackTactic.PERSISTENCE: ft.Colors.DEEP_ORANGE_700,
    AttackTactic.PRIVILEGE_ESCALATION: ft.Colors.PURPLE_700,
    AttackTactic.DEFENSE_EVASION: ft.Colors.TEAL_700,
    AttackTactic.CREDENTIAL_ACCESS: ft.Colors.PINK_700,
    AttackTactic.DISCOVERY: ft.Colors.CYAN_700,
    AttackTactic.LATERAL_MOVEMENT: ft.Colors.LIME_700,
    AttackTactic.COLLECTION: ft.Colors.AMBER_700,
    AttackTactic.COMMAND_AND_CONTROL: ft.Colors.GREEN_700,
    AttackTactic.EXFILTRATION: ft.Colors.LIGHT_BLUE_700,
    AttackTactic.IMPACT: ft.Colors.BROWN_700,
}


def _badge(text: str, color: ft.Colors) -> ft.Container:
    return ft.Container(
        ft.Text(text, size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
        bgcolor=color,
        border_radius=12,
        padding=ft.Padding(left=8, right=8, top=3, bottom=3),
    )


@ft.component
def ModuleCard(class_key: str, module: APT_MODULE):
    def on_toggle(e: ft.Event[ft.Switch]):
        module.enable(e.control.value)

    tactic_color = TACTIC_COLORS.get(module.tactic, ft.Colors.GREY_700)

    # OS / Arch compatibility chips – only shown when not "Any"
    compat_chips: list[ft.Control] = []
    if not (len(module.compatible_os) == 1 and module.compatible_os[0] == TargetOS.ANY):
        for os_val in module.compatible_os:
            compat_chips.append(_badge(os_val.value, ft.Colors.BLUE_GREY_700))
    if not (len(module.compatible_arch) == 1 and module.compatible_arch[0] == TargetArch.ANY):
        for arch_val in module.compatible_arch:
            compat_chips.append(_badge(arch_val.value, ft.Colors.GREY_700))

    left_column = ft.Column(
        [
            ft.Text(module.name or class_key, weight=ft.FontWeight.BOLD, size=15),
            ft.Text(
                module.description,
                size=12,
                color=ft.Colors.GREY_400,
                no_wrap=False,
            ),
            ft.Row(
                [
                    _badge(module.tactic.display_name, tactic_color),
                    ft.Text(
                        f"{module.technique_id}  {module.technique_name}",
                        size=11,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    ),
                ],
                wrap=True,
                spacing=6,
                run_spacing=4,
            ),
            *([ft.Row(compat_chips, spacing=6, wrap=True)] if compat_chips else []),
        ],
        spacing=6,
        expand=True,
        expand_loose=True,
    )

    return ft.Container(
        ft.Row(
            [
                left_column,
                ft.Switch(value=module.enabled, on_change=on_toggle),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        bgcolor=ft.Colors.GREY_900,
        border_radius=10,
        padding=12,
        margin=ft.Margin(left=0, right=0, top=4, bottom=4),
    )

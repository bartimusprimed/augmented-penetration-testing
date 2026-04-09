import flet as ft
from models.module_metadata import AttackTactic
from modules.base_module import APT_MODULE
from components.modules.module_card import ModuleCard, TACTIC_COLORS


@ft.component
def TacticSection(tactic: AttackTactic, modules: dict[str, APT_MODULE]):
    enabled_count = sum(1 for m in modules.values() if m.enabled)
    tactic_color = TACTIC_COLORS.get(tactic, ft.Colors.GREY_700)

    title_row = ft.Row(
        [
            ft.Text(tactic.display_name, weight=ft.FontWeight.BOLD, size=15),
            ft.Container(
                ft.Text(tactic.tactic_id, size=11, color=ft.Colors.WHITE),
                bgcolor=tactic_color,
                border_radius=8,
                padding=ft.Padding(left=7, right=7, top=2, bottom=2),
            ),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    subtitle = ft.Text(
        f"{enabled_count} of {len(modules)} enabled",
        size=12,
        color=ft.Colors.GREY_400,
    )

    cards = [ModuleCard(class_key=k, module=v) for k, v in modules.items()]

    return ft.ExpansionTile(
        title=title_row,
        subtitle=subtitle,
        controls=cards,
        expanded=True,
        controls_padding=ft.Padding(left=8, right=8, top=0, bottom=8),
        bgcolor=ft.Colors.GREY_900,
        collapsed_bgcolor=ft.Colors.GREY_900,
    )

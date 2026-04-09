import flet as ft
from models.chain import Chain
from models.apt import Apt

CYAN = ft.Colors.CYAN_400


@ft.component
def ChainCard(chain: Chain, state: Apt, on_select):
    module_count = len(chain.module_keys)
    mod_names = []
    for key in chain.module_keys[:3]:
        mod = state.modules.classes.get(key)
        mod_names.append(mod.name if mod and mod.name else key)
    if module_count > 3:
        mod_names.append(f"+{module_count - 3} more")

    preview = " → ".join(mod_names) if mod_names else "Empty chain"

    return ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(chain.name, weight=ft.FontWeight.BOLD, size=14, color=CYAN, expand=True),
                        ft.Text(f"{module_count} step{'s' if module_count != 1 else ''}", size=11, color=ft.Colors.GREY_500),
                    ],
                ),
                ft.Text(preview, size=12, color=ft.Colors.GREY_400, no_wrap=False),
            ],
            spacing=6,
        ),
        bgcolor=ft.Colors.GREY_900,
        border_radius=10,
        padding=12,
        margin=ft.Margin(bottom=6, top=0, left=0, right=0),
        on_click=lambda _: on_select(chain),
        ink=True,
        border=ft.Border.all(1, ft.Colors.GREY_800),
    )

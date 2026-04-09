import flet as ft
from models.chain import Chain
from models.apt import Apt

CYAN = ft.Colors.CYAN_400
NODE_BG = "#1a2d3d"
DRAG_BG = "#0d3050"


def _module_node(key: str, mod, chain: Chain, index: int, total: int) -> ft.Control:
    """A single module node in the chain builder with reorder controls."""
    name = (mod.name if mod and mod.name else key)
    desc = (mod.description[:60] + "…" if mod and mod.description and len(mod.description) > 60 else (mod.description if mod else ""))

    return ft.Draggable(
        group="chain_node",
        data=key,
        content=ft.Container(
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.IconButton(
                                ft.Icons.ARROW_UPWARD,
                                icon_size=16,
                                icon_color=ft.Colors.GREY_500,
                                on_click=lambda _, k=key: chain.move_up(k),
                                disabled=index == 0,
                                style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
                            ),
                            ft.IconButton(
                                ft.Icons.ARROW_DOWNWARD,
                                icon_size=16,
                                icon_color=ft.Colors.GREY_500,
                                on_click=lambda _, k=key: chain.move_down(k),
                                disabled=index == total - 1,
                                style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
                            ),
                        ],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Column(
                        [
                            ft.Text(name, weight=ft.FontWeight.BOLD, size=13, color=CYAN),
                            ft.Text(desc, size=11, color=ft.Colors.GREY_400, no_wrap=False) if desc else ft.Container(),
                        ],
                        expand=True,
                        spacing=3,
                    ),
                    ft.IconButton(
                        ft.Icons.REMOVE_CIRCLE_OUTLINE,
                        icon_size=18,
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda _, k=key: chain.remove_module(k),
                        tooltip="Remove from chain",
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=NODE_BG,
            border_radius=8,
            padding=10,
            border=ft.Border.all(1, ft.Colors.CYAN_900),
        ),
        content_when_dragging=ft.Container(
            ft.Text(name, size=13, color=CYAN),
            bgcolor=DRAG_BG,
            border_radius=8,
            padding=10,
            opacity=0.7,
            border=ft.Border.all(1, CYAN),
        ),
    )


def _arrow() -> ft.Control:
    return ft.Column(
        [
            ft.Container(width=2, height=16, bgcolor=ft.Colors.CYAN_900),
            ft.Icon(ft.Icons.ARROW_DOWNWARD, size=16, color=ft.Colors.CYAN_700),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
    )


@ft.component
def ChainBuilder(chain: Chain, state: Apt):
    nodes: list[ft.Control] = []
    total = len(chain.module_keys)

    for i, key in enumerate(chain.module_keys):
        mod = state.modules.classes.get(key)
        nodes.append(_module_node(key, mod, chain, i, total))
        if i < total - 1:
            nodes.append(_arrow())

    def on_drop(e: ft.DragTargetEvent):
        key = e.src.data if e.src is not None and e.src_id is not None else None
        if key and key not in chain.module_keys:
            chain.add_module(key)

    drop_zone = ft.DragTarget(
        group="chain_node",
        on_accept=on_drop,
        content=ft.Container(
            ft.Column(
                [
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=ft.Colors.CYAN_900, size=32),
                    ft.Text("Drop module here to add to chain", size=12, color=ft.Colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
            ),
            bgcolor=ft.Colors.GREY_900,
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.GREY_700),
            padding=16,
            alignment=ft.Alignment.CENTER,
        ),
    )

    async def run_chain(e):
        await state.run_chain(chain, e)

    return ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(chain.name, size=16, weight=ft.FontWeight.BOLD, color=CYAN),
                        ft.Row(
                            [
                                ft.Button(
                                    "Run Chain",
                                    on_click=run_chain,
                                    bgcolor=CYAN,
                                    color=ft.Colors.BLACK,
                                    disabled=total == 0,
                                ),
                                ft.Button(
                                    "Clear",
                                    on_click=lambda _: chain.clear(),
                                    bgcolor=ft.Colors.GREY_800,
                                ),
                            ],
                            spacing=8,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=1, bgcolor=ft.Colors.GREY_800),
                ft.Column(nodes, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True) if nodes else ft.Container(),
                drop_zone,
            ],
            expand=True,
            spacing=12,
        ),
        expand=True,
        padding=16,
        bgcolor=ft.Colors.GREY_900,
        border_radius=12,
    )

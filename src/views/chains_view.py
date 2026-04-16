import flet as ft
import time
from models.apt import Apt
from models.chain import Chain
from components.chains.chain_card import ChainCard
from components.chains.chain_canvas import ChainCanvas
from components.chains.module_palette import ModulePalette

CYAN = ft.Colors.CYAN_400


@ft.component
def Chains(state: Apt):
    selected_chain, set_selected_chain = ft.use_state(None)
    chain_name_input, set_chain_name_input = ft.use_state("")

    def _fmt_saved(ts: float) -> str:
        if ts <= 0:
            return "never"
        return time.strftime("%H:%M:%S", time.localtime(ts))

    def select_chain(chain: Chain):
        set_selected_chain(chain)
        set_chain_name_input(chain.name)

    def add_chain(e):
        new_chain = state.create_chain(f"Chain {len(state.chains) + 1}")
        set_selected_chain(new_chain)
        set_chain_name_input(new_chain.name)

    def delete_chain(e):
        if selected_chain is not None:
            state.remove_chain(selected_chain)
            set_selected_chain(None)
            set_chain_name_input("")

    def delete_chain_item(chain: Chain):
        state.remove_chain(chain)
        if selected_chain == chain:
            set_selected_chain(None)
            set_chain_name_input("")

    def on_chain_name_change(e: ft.ControlEvent):
        set_chain_name_input(e.control.value or "")

    def rename_selected_chain(e: ft.ControlEvent):
        if selected_chain is None:
            return
        new_name = (chain_name_input or "").strip()
        if not new_name:
            set_chain_name_input(selected_chain.name)
            return
        if selected_chain.name != new_name:
            selected_chain.name = new_name
            selected_chain.trigger_update()
        set_chain_name_input(selected_chain.name)

    chain_list_items: list[ft.Control] = [
        ft.Row(
            [
                ft.Text("Chains", size=18, weight=ft.FontWeight.BOLD, color=CYAN, expand=True),
                ft.IconButton(
                    ft.Icons.ADD,
                    icon_color=CYAN,
                    tooltip="New Chain",
                    on_click=add_chain,
                ),
            ],
        ),
        ft.Row(
            [
                ft.Icon(
                    ft.Icons.CHECK_CIRCLE if state.chains_save_status in ("Saved", "Loaded") else ft.Icons.ERROR_OUTLINE,
                    size=12,
                    color=ft.Colors.GREEN_400 if state.chains_save_status in ("Saved", "Loaded") else ft.Colors.RED_400,
                ),
                ft.Text(
                    f"{state.chains_save_status} at {_fmt_saved(state.chains_last_saved_at)}",
                    size=11,
                    color=ft.Colors.GREY_500,
                ),
            ],
            spacing=4,
        ),
        ft.Container(height=1, bgcolor=ft.Colors.GREY_800),
    ]

    selected_count = len(state.get_selected_targets())
    chain_list_items.append(
        ft.Container(
            ft.Row(
                [
                    ft.Icon(
                        ft.Icons.ADJUST,
                        size=14,
                        color=ft.Colors.GREEN_400 if selected_count > 0 else ft.Colors.GREY_600,
                    ),
                    ft.Text(
                        f"{selected_count} target{'s' if selected_count != 1 else ''} selected",
                        size=12,
                        color=ft.Colors.GREEN_400 if selected_count > 0 else ft.Colors.GREY_600,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.Padding(left=2, right=2, top=4, bottom=4),
        )
    )
    for chain in state.chains:
        chain_list_items.append(
            ChainCard(
                chain=chain,
                state=state,
                on_select=select_chain,
                on_delete=delete_chain_item,
            )
        )

    if not state.chains:
        chain_list_items.append(
            ft.Container(
                ft.Column(
                    [
                        ft.Icon(ft.Icons.LINK_OFF, color=ft.Colors.GREY_700, size=36),
                        ft.Text("No chains yet", size=13, color=ft.Colors.GREY_600),
                        ft.Text("Click + to create one", size=11, color=ft.Colors.GREY_700),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
                alignment=ft.Alignment.CENTER,
                padding=24,
            )
        )

    chains_sidebar = ft.Container(
        ft.Column(chain_list_items, spacing=4, scroll=ft.ScrollMode.AUTO, expand=True),
        width=220,
        bgcolor=ft.Colors.GREY_900,
        border_radius=12,
        padding=12,
        border=ft.Border(right=ft.BorderSide(1, ft.Colors.GREY_800)),
    )

    if selected_chain is not None:
        right_panel = ft.Row(
            [
                ModulePalette(state),
                ft.Container(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.LINK, color=CYAN, size=20),
                                    ft.TextField(
                                        value=chain_name_input,
                                        text_size=18,
                                        on_change=on_chain_name_change,
                                        on_submit=rename_selected_chain,
                                        on_blur=rename_selected_chain,
                                        border_color=ft.Colors.GREY_700,
                                        focused_border_color=CYAN,
                                        bgcolor=ft.Colors.GREY_900,
                                        dense=True,
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        ft.Icons.DELETE_OUTLINE,
                                        icon_color=ft.Colors.RED_400,
                                        tooltip="Delete chain",
                                        on_click=delete_chain,
                                    ),
                                ],
                                spacing=8,
                            ),
                            ft.Text(
                                "Drag modules from the left panel onto the canvas. Drag canvas nodes to reposition them.",
                                size=12,
                                color=ft.Colors.GREY_500,
                            ),
                            ChainCanvas(chain=selected_chain, state=state),
                        ],
                        expand=True,
                        spacing=12,
                    ),
                    expand=True,
                    padding=16,
                ),
            ],
            expand=True,
            spacing=0,
        )
    else:
        right_panel = ft.Container(
            ft.Column(
                [
                    ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, color=ft.Colors.GREY_700, size=64),
                    ft.Text("Select a chain to edit", size=16, color=ft.Colors.GREY_500),
                    ft.Text(
                        "Create a chain of modules to run in sequence against your selected targets.",
                        size=13,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Button(
                        "Create First Chain",
                        on_click=add_chain,
                        bgcolor=CYAN,
                        color=ft.Colors.BLACK,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
            expand=True,
            alignment=ft.Alignment.CENTER,
        )

    return ft.Container(
        ft.Row(
            [
                chains_sidebar,
                right_panel,
            ],
            expand=True,
            spacing=0,
        ),
        expand=True,
        padding=16,
    )

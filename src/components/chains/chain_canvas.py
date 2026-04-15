"""ChainCanvas — drag-and-drop DAG canvas for building attack chains.

Modules are dragged from ModulePalette onto the canvas where they become
positioned ChainNode cards.  Prerequisite warnings are shown when a node's
``consumes`` facts are not produced by any upstream node.
"""
import flet as ft
from models.chain import Chain
from models.apt import Apt
from components.chains.chain_node_card import ChainNodeCard

CYAN = ft.Colors.CYAN_400
CANVAS_BG = "#0d1b24"
GRID_COLOR = "#111e27"

# Spacing for auto-layout when a node is dropped without an explicit position
_AUTO_LAYOUT_X_START = 20.0
_AUTO_LAYOUT_Y_START = 20.0
_AUTO_LAYOUT_X_STEP = 220.0
_AUTO_LAYOUT_Y_STEP = 160.0


def _auto_position(chain: Chain) -> tuple[float, float]:
    """Return a sensible default position for a newly dropped node."""
    count = len(chain.nodes)
    col = count % 4
    row = count // 4
    return (
        _AUTO_LAYOUT_X_START + col * _AUTO_LAYOUT_X_STEP,
        _AUTO_LAYOUT_Y_START + row * _AUTO_LAYOUT_Y_STEP,
    )


@ft.component
def ChainCanvas(chain: Chain, state: Apt):
    """Main canvas component for composing attack chains as a DAG."""

    # Collect prerequisite warnings
    warnings = chain.validate_prerequisites(state.modules)

    # Build node cards
    node_cards: list[ft.Control] = [
        ChainNodeCard(node=node, chain=chain, state=state)
        for node in chain.nodes.values()
    ]

    def on_module_drop(e: ft.DragTargetEvent):
        """A module key was dropped from the palette onto the canvas."""
        module_key = e.src.data if e.src is not None else None
        if not module_key:
            return
        pos = _auto_position(chain)
        chain.add_node(module_key, position=pos)

    drop_overlay = ft.DragTarget(
        group="chain_node",
        on_accept=on_module_drop,
        content=ft.Container(
            expand=True,
            bgcolor=ft.Colors.TRANSPARENT,
        ),
    )

    # Stack: background grid + nodes + invisible drop overlay on top
    canvas_stack = ft.Stack(
        [
            # Grid background
            ft.Container(
                expand=True,
                bgcolor=CANVAS_BG,
            ),
            # Node cards (positioned absolutely via left/top on each card)
            *node_cards,
            # Drop overlay — must be last so it catches drops anywhere
            drop_overlay,
        ],
        expand=True,
    )

    # Prerequisite warning banner
    warning_items: list[ft.Control] = []
    for w in warnings:
        warning_items.append(
            ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER_400, size=14),
                    ft.Text(w, size=11, color=ft.Colors.AMBER_400, expand=True, no_wrap=False),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        )

    warning_banner: ft.Control = ft.Container()
    if warning_items:
        warning_banner = ft.Container(
            ft.Column(warning_items, spacing=4),
            bgcolor="#1a1400",
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.AMBER_800),
            padding=ft.Padding(left=10, right=10, top=8, bottom=8),
            margin=ft.Margin(bottom=8, top=0, left=0, right=0),
        )

    empty_hint: ft.Control = ft.Container()
    if not chain.nodes:
        empty_hint = ft.Container(
            ft.Column(
                [
                    ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, color=ft.Colors.GREY_700, size=48),
                    ft.Text("Drag modules here to build the chain", size=13, color=ft.Colors.GREY_600),
                    ft.Text(
                        "Connect nodes: drag from one node's output to another's input once edge-creation UI is added.",
                        size=11,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )
        # Replace stack with hint when empty
        canvas_stack = ft.Stack(
            [
                ft.Container(expand=True, bgcolor=CANVAS_BG),
                empty_hint,
                drop_overlay,
            ],
            expand=True,
        )

    return ft.Column(
        [
            warning_banner,
            ft.Container(
                canvas_stack,
                expand=True,
                border_radius=10,
                border=ft.Border.all(1, ft.Colors.GREY_800),
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
        ],
        expand=True,
        spacing=0,
    )

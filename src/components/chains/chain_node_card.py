"""ChainNodeCard — a draggable node widget for the chain canvas.

Displays module name, tactic badge, and consumes/produces fact pills.
The card can be positioned absolutely within a ft.Stack canvas.
"""
import flet as ft
from models.chain import Chain
from models.chain_node import ChainNode
from models.apt import Apt
from models.module_metadata import AttackTactic

CYAN = ft.Colors.CYAN_400
NODE_BG = "#1a2d3d"
NODE_BORDER = ft.Colors.CYAN_900
NODE_RUNNING_BORDER = ft.Colors.AMBER_400
NODE_SUCCESS_BORDER = ft.Colors.GREEN_400
NODE_FAILED_BORDER = ft.Colors.RED_400

_TACTIC_COLORS: dict[AttackTactic, str] = {
    AttackTactic.RECONNAISSANCE: ft.Colors.CYAN_700,
    AttackTactic.RESOURCE_DEVELOPMENT: ft.Colors.BLUE_700,
    AttackTactic.INITIAL_ACCESS: ft.Colors.ORANGE_700,
    AttackTactic.EXECUTION: ft.Colors.RED_700,
    AttackTactic.PERSISTENCE: ft.Colors.PURPLE_700,
    AttackTactic.PRIVILEGE_ESCALATION: ft.Colors.DEEP_ORANGE_700,
    AttackTactic.DEFENSE_EVASION: ft.Colors.TEAL_700,
    AttackTactic.CREDENTIAL_ACCESS: ft.Colors.PINK_700,
    AttackTactic.DISCOVERY: ft.Colors.INDIGO_700,
    AttackTactic.LATERAL_MOVEMENT: ft.Colors.AMBER_700,
    AttackTactic.COLLECTION: ft.Colors.GREEN_700,
    AttackTactic.COMMAND_AND_CONTROL: ft.Colors.LIME_700,
    AttackTactic.EXFILTRATION: ft.Colors.BROWN_700,
    AttackTactic.IMPACT: ft.Colors.DEEP_ORANGE_900,
}


def _status_color(status: str) -> str:
    match status:
        case "running":
            return NODE_RUNNING_BORDER
        case "success":
            return NODE_SUCCESS_BORDER
        case "failed":
            return NODE_FAILED_BORDER
        case _:
            return NODE_BORDER


def _fact_pill(label: str, color: str) -> ft.Control:
    return ft.Container(
        ft.Text(label, size=9, color=ft.Colors.WHITE),
        bgcolor=color,
        border_radius=10,
        padding=ft.Padding(left=6, right=6, top=2, bottom=2),
    )


def ChainNodeCard(node: ChainNode, chain: Chain, state: Apt) -> ft.Control:
    """Build a positioned, draggable node card for the canvas.

    This is a plain function (not @ft.component) because it is used inside
    the ft.Stack children list which is built in a @ft.component render pass.
    """
    mod = state.modules.classes.get(node.module_key)
    name = (mod.name if mod and mod.name else node.module_key)
    tactic = mod.tactic if mod else None
    consumes = mod.consumes if mod else []
    produces = mod.produces if mod else []

    border_color = _status_color(node.status)

    tactic_badge = ft.Container()
    if tactic:
        color = _TACTIC_COLORS.get(tactic, ft.Colors.GREY_700)
        tactic_badge = ft.Container(
            ft.Text(tactic.display_name, size=9, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=color,
            border_radius=4,
            padding=ft.Padding(left=5, right=5, top=2, bottom=2),
        )

    fact_row_items: list[ft.Control] = []
    for f in consumes:
        fact_row_items.append(_fact_pill(f"← {f}", ft.Colors.ORANGE_800))
    for f in produces:
        fact_row_items.append(_fact_pill(f"→ {f}", ft.Colors.GREEN_800))

    fact_row = ft.Row(fact_row_items, spacing=4, wrap=True) if fact_row_items else ft.Container()

    card_content = ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(name, weight=ft.FontWeight.BOLD, size=13, color=CYAN, expand=True),
                        ft.IconButton(
                            ft.Icons.CLOSE,
                            icon_size=14,
                            icon_color=ft.Colors.RED_400,
                            on_click=lambda _, nid=node.node_id: chain.remove_node(nid),
                            tooltip="Remove node",
                            style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
                        ),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                tactic_badge,
                fact_row,
            ],
            spacing=4,
            tight=True,
        ),
        bgcolor=NODE_BG,
        border_radius=8,
        padding=10,
        border=ft.Border.all(1, border_color),
        width=180,
    )

    return ft.Container(
        ft.Draggable(
            group="canvas_node",
            data=node.node_id,
            content=card_content,
            content_when_dragging=ft.Container(
                ft.Text(name, size=13, color=CYAN),
                bgcolor="#0d3050",
                border_radius=8,
                padding=10,
                opacity=0.7,
                border=ft.Border.all(1, CYAN),
                width=180,
            ),
        ),
        left=node.position[0],
        top=node.position[1],
    )

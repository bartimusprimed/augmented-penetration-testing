import flet as ft
import time
from typing import cast
from models.target import Target, MESSAGE_TYPE
from models.apt import Apt

CYAN = ft.Colors.CYAN_400


def _fmt_last_seen(ts: float) -> str:
    if ts == 0.0:
        return "never"
    delta = int(time.time() - ts)
    if delta < 60:
        return f"{delta}s ago"
    if delta < 3600:
        return f"{delta // 60}m ago"
    return f"{delta // 3600}h ago"


def _activity_color(message_type: MESSAGE_TYPE) -> str:
    match message_type:
        case MESSAGE_TYPE.SUCCESS:
            return ft.Colors.GREEN_400
        case MESSAGE_TYPE.ERROR:
            return ft.Colors.RED_400
        case _:
            return ft.Colors.AMBER_400


def _is_beacon_entry(message: str) -> bool:
    msg = message.lower()
    return "beacon" in msg or "c2 server" in msg


def _build_activity_item(entry) -> ft.Control:
    ts = time.strftime("%H:%M:%S", time.localtime(entry.timestamp)) if entry.timestamp else "--:--:--"
    color = _activity_color(entry.message_type)
    title = f"[{ts}] {entry.message}"

    if entry.details:
        return ft.Container(
            ft.ExpansionTile(
                title=ft.Text(title, color=color, size=12),
                controls=[
                    ft.Container(
                        ft.Text(
                            entry.details,
                            selectable=True,
                            color=ft.Colors.GREY_300,
                            font_family="monospace",
                            size=12,
                        ),
                        padding=ft.Padding(left=8, right=8, top=4, bottom=8),
                    )
                ],
                collapsed_text_color=color,
                text_color=color,
            ),
            bgcolor=ft.Colors.GREY_900,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.GREY_800),
            margin=ft.Margin(bottom=6, top=0, left=0, right=0),
        )

    return ft.Container(
        ft.Text(title, selectable=True, color=color, size=12),
        bgcolor=ft.Colors.GREY_900,
        border_radius=8,
        border=ft.Border.all(1, ft.Colors.GREY_800),
        padding=ft.Padding(left=10, right=10, top=8, bottom=8),
        margin=ft.Margin(bottom=6, top=0, left=0, right=0),
    )


def _overview_tab_content(t: Target):
    """Activity log list.

    Plain function called from within TargetDetailsContent which is a
    @ft.component — observable reads here are tracked by the parent.
    """
    entries: list[ft.Control] = []
    beacon_entries = [entry for entry in t.activity_log if _is_beacon_entry(entry.message)]
    regular_entries = [entry for entry in t.activity_log if not _is_beacon_entry(entry.message)]

    for entry in regular_entries:
        entries.append(_build_activity_item(entry))

    if beacon_entries:
        beacon_children = [
            ft.Container(
                ft.Text(
                    f"[{time.strftime('%H:%M:%S', time.localtime(entry.timestamp)) if entry.timestamp else '--:--:--'}] {entry.message}",
                    selectable=True,
                    color=_activity_color(entry.message_type),
                    size=12,
                ),
                margin=ft.Margin(bottom=4, top=0, left=0, right=0),
            )
            for entry in beacon_entries
        ]
        entries.append(
            ft.Container(
                ft.ExpansionTile(
                    title=ft.Text(f"Beacon Log ({len(beacon_entries)} entries)", color=ft.Colors.AMBER_400, size=12),
                    controls=[
                        ft.Container(
                            ft.Column(beacon_children, spacing=0),
                            padding=ft.Padding(left=8, right=8, top=4, bottom=8),
                        )
                    ],
                    collapsed_text_color=ft.Colors.AMBER_400,
                    text_color=ft.Colors.AMBER_400,
                ),
                bgcolor=ft.Colors.GREY_900,
                border_radius=8,
                border=ft.Border.all(1, ft.Colors.GREY_800),
                margin=ft.Margin(bottom=6, top=0, left=0, right=0),
            )
        )

    if not entries:
        entries = [ft.Text("No activity yet", color=ft.Colors.GREY_600)]

    return ft.Container(
        ft.ListView(entries, expand=True, spacing=2),
        expand=True,
        padding=ft.Padding(left=4, right=4, top=8, bottom=8),
    )


def _shell_tab_content(t: Target, state: Apt):
    """Emulated shell: send commands to beacon, view output history.

    Plain function called from within the TargetDetailsContent @ft.component,
    which tracks observable reads for reactivity.  Uses a direct reference to
    the TextField widget (instead of ft.use_state) so the send_command handler
    can read/clear its value imperatively from an event callback context.
    """

    # send_command is defined before cmd_field; Python closures resolve
    # free variables at call-time, so cmd_field will be bound by the time
    # the user actually clicks "Send" or presses Enter.
    def send_command(e):
        cmd = (cmd_field.value or "").strip()
        if not cmd or not t.beacon_session_id:
            return
        # Use the beacon module's public push_command method
        beacon_mod = state.modules.classes.get("beacon")
        if beacon_mod and beacon_mod.push_command(t.beacon_session_id, cmd):
            t.log_activity(
                f"Task queued: {cmd}",
                message_type=MESSAGE_TYPE.INFORMATION,
                details="Queued for next beacon check-in.",
            )
            cast(ft.Observable, t).notify()
        cmd_field.value = ""

    cmd_field = ft.TextField(
        hint_text="Enter shell command…",
        expand=True,
        dense=True,
        on_submit=send_command,
        border_color=CYAN,
        focused_border_color=CYAN,
        disabled=not t.beacon_connected,
    )

    task_entries = [
        entry
        for entry in t.activity_log
        if entry.message.startswith("Task queued:") or entry.message.startswith("Task:")
    ]
    history_items = [_build_activity_item(entry) for entry in reversed(task_entries)]
    if not history_items:
        history_items = [
            ft.Container(
                ft.Text("No tasks queued or executed yet.", color=ft.Colors.GREY_600, size=12),
                padding=ft.Padding(left=8, right=8, top=8, bottom=8),
            )
        ]

    not_connected_msg = (
        ft.Container(
            ft.Column(
                [
                    ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.GREY_700, size=40),
                    ft.Text("No active beacon session", color=ft.Colors.GREY_500, size=13),
                    ft.Text(
                        "Run the 'C2 Beacon' module to start a beacon on this target.",
                        color=ft.Colors.GREY_700,
                        size=11,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=24,
        )
        if not t.beacon_connected
        else ft.Container()
    )

    return ft.Column(
        [
            not_connected_msg,
            ft.Container(
                ft.ListView(history_items, expand=True, spacing=2),
                expand=True,
                bgcolor=ft.Colors.GREY_900,
                border_radius=8,
                padding=8,
            ),
            ft.Row(
                [
                    cmd_field,
                    ft.IconButton(
                        ft.Icons.SEND,
                        icon_color=CYAN,
                        on_click=send_command,
                        disabled=not t.beacon_connected,
                        tooltip="Send command",
                    ),
                ],
                spacing=8,
            ),
        ],
        expand=True,
        spacing=8,
    )


def _beacon_tab_content(t: Target):
    """Beacon status and configuration."""
    status_color = ft.Colors.GREEN_400 if t.beacon_connected else ft.Colors.GREY_600
    status_label = "Connected" if t.beacon_connected else "Not connected"

    def on_interval_change(e: ft.Event[ft.TextField]):
        try:
            val = int(e.control.value)
            if val > 0:
                t.update_field("beacon_interval", val)
        except ValueError:
            pass

    def on_port_change(e: ft.Event[ft.TextField]):
        try:
            val = int(e.control.value)
            if 1 <= val <= 65535:
                t.update_field("beacon_c2_port", val)
        except ValueError:
            pass

    return ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CIRCLE, color=status_color, size=14),
                        ft.Text(status_label, size=13, color=status_color),
                    ],
                    spacing=6,
                ),
                ft.Divider(color=ft.Colors.GREY_800),
                ft.Text("Session ID", size=11, color=ft.Colors.GREY_500),
                ft.Text(t.beacon_session_id or "—", selectable=True, size=12),
                ft.Text("Last check-in", size=11, color=ft.Colors.GREY_500),
                ft.Text(_fmt_last_seen(t.beacon_last_seen), size=12),
                ft.Divider(color=ft.Colors.GREY_800),
                ft.Text("C2 port", size=11, color=ft.Colors.GREY_500),
                ft.TextField(
                    value=str(t.beacon_c2_port),
                    on_blur=on_port_change,
                    on_submit=on_port_change,
                    dense=True,
                    width=120,
                    keyboard_type=ft.KeyboardType.NUMBER,
                ),
                ft.Text("Check-in interval (seconds)", size=11, color=ft.Colors.GREY_500),
                ft.TextField(
                    value=str(t.beacon_interval),
                    on_blur=on_interval_change,
                    on_submit=on_interval_change,
                    dense=True,
                    width=120,
                    keyboard_type=ft.KeyboardType.NUMBER,
                ),
            ],
            spacing=6,
        ),
        padding=ft.Padding(left=4, right=4, top=8, bottom=8),
        expand=True,
    )


def TargetDetailsContent(t: Target, state: Apt):
    """Build the dialog content for Target Details.

    This is a plain function — NOT a @ft.component — because it is called from
    show_target_details which is an on_click event handler.  Event handlers run
    outside the Flet renderer context, so instantiating a @ft.component from
    one crashes with 'RuntimeError: No current renderer is set'.
    """
    return ft.Container(
        ft.Tabs(
            content=ft.Column(
                [
                    ft.TabBar(
                        tabs=[
                            ft.Tab("Overview", icon=ft.Icons.LIST_ALT_OUTLINED),
                            ft.Tab("Shell", icon=ft.Icons.TERMINAL),
                            ft.Tab("Beacon", icon=ft.Icons.WIFI_TETHERING),
                        ],
                    ),
                    ft.TabBarView(
                        controls=[
                            _overview_tab_content(t=t),
                            _shell_tab_content(t=t, state=state),
                            _beacon_tab_content(t=t),
                        ],
                        expand=True,
                    ),
                ],
                expand=True,
                spacing=0,
            ),
            length=3,
            expand=True,
        ),
        expand=True,
        height=420,
        width=520,
    )


@ft.component
def target(t: Target, state: Apt):
    def show_target_details(e: ft.Event[ft.Button]):
        import asyncio

        selected_target = t
        dialog_state = {"open": True}

        def close_dialog(_: ft.Event[ft.TextButton] | None = None):
            dialog_state["open"] = False

        def dismiss_dialog(_: ft.Event[ft.TextButton] | None = None):
            close_dialog()
            ft.context.page.pop_dialog()

        def delete_target(_: ft.Event[ft.TextButton]):
            dialog_state["open"] = False
            state.remove_target(selected_target)

        dialog = ft.AlertDialog(
            title=ft.Text(f"Target: {t.ip_label}"),
            alignment=ft.Alignment.CENTER,
            icon=ft.Icon(ft.Icons.INFO_OUTLINED),
            content=TargetDetailsContent(t=selected_target, state=state),
            actions=[
                ft.TextButton(
                    "Delete Target",
                    on_click=delete_target,
                    style=ft.ButtonStyle(color=ft.Colors.RED_400),
                ),
                ft.TextButton("Close", on_click=dismiss_dialog),
            ],
        )
        dialog.on_dismiss = lambda _: close_dialog()

        async def refresh_dialog():
            while dialog_state["open"]:
                try:
                    dialog.content = TargetDetailsContent(t=selected_target, state=state)
                    dialog.update()
                except Exception:
                    dialog_state["open"] = False
                    break
                await asyncio.sleep(1)

        ft.context.page.show_dialog(dialog)
        ft.context.page.run_task(refresh_dialog)

    def update_target_field_and_notify(e: ft.Event[ft.Checkbox]):
        t.update_field("is_selected", e.control.value)
        state.trigger_update()

    target_ip = ft.Text(t.ip_label, weight=ft.FontWeight.BOLD, size=16, width=140)
    target_status = ft.Text(
        t.current_status,
        no_wrap=True,
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS,
        text_align=ft.TextAlign.LEFT,
        size=12,
        width=420,
    )

    beacon_indicator = (
        ft.Icon(ft.Icons.WIFI_TETHERING, color=ft.Colors.GREEN_400, size=14, tooltip="Beacon connected")
        if t.beacon_connected
        else ft.Container()
    )

    return ft.Container(
        ft.Row(
            [
                ft.Checkbox(
                    label="Selected",
                    value=t.is_selected,
                    on_change=update_target_field_and_notify,
                    label_position=ft.LabelPosition.RIGHT,
                    width=120,
                ),
                ft.Row([target_ip, beacon_indicator], spacing=6, width=170),
                ft.Container(target_status, expand=True),
                ft.Button(
                    "Target Details",
                    data=t.ip_label,
                    on_click=show_target_details,
                    elevation=3,
                    bgcolor=ft.Colors.BLUE_GREY,
                    width=140,
                ),
            ],
            spacing=12,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(left=12, right=12, top=8, bottom=8),
        border_radius=10,
        bgcolor=t.color_status,
        border=ft.Border.all(1, ft.Colors.GREY_800),
    )

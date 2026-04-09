import flet as ft

CYAN = ft.Colors.CYAN_400


def _step(number: str, text: str) -> ft.Control:
    return ft.Row(
        [
            ft.Container(
                ft.Text(number, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                bgcolor=CYAN,
                width=28,
                height=28,
                border_radius=14,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Text(text, size=14, color=ft.Colors.GREY_300, expand=True, no_wrap=False),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )


@ft.component
def Workflow():
    return ft.Container(
        ft.Column(
            [
                ft.Text("Workflow", size=18, weight=ft.FontWeight.BOLD, color=CYAN),
                _step("1", "Add targets via the Targets tab and select them. Use Ping or Port Scan modules to discover live hosts."),
                _step("2", "Enable modules on the Modules page. Run enabled modules against selected targets using the action buttons."),
                _step("3", "Build automation chains in the Chains tab by dragging modules into a sequence, then run the full chain on targets."),
                _step("4", "View results in the activity log for each target via Target Details."),
            ],
            spacing=14,
        ),
        bgcolor=ft.Colors.GREY_900,
        border_radius=12,
        padding=20,
    )

import flet as ft
from models.apt import Apt

CYAN = ft.Colors.CYAN_400


@ft.component
def Settings(state: Apt):
    return ft.Container(
        ft.Column(
            [
                ft.Text("Settings", size=22, weight=ft.FontWeight.BOLD, color=CYAN),
                ft.Container(
                    ft.Column(
                        [
                            ft.Text("Application", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300),
                            ft.Container(height=1, bgcolor=ft.Colors.GREY_800),
                            ft.Row(
                                [
                                    ft.Text("Version", size=13, color=ft.Colors.GREY_400, expand=True),
                                    ft.Text(state.version, size=13, color=ft.Colors.GREY_300),
                                ],
                            ),
                            ft.Row(
                                [
                                    ft.Text("Product Name", size=13, color=ft.Colors.GREY_400, expand=True),
                                    ft.Text(state.title, size=13, color=ft.Colors.GREY_300),
                                ],
                            ),
                        ],
                        spacing=10,
                    ),
                    bgcolor=ft.Colors.GREY_900,
                    border_radius=12,
                    padding=16,
                ),
                ft.Container(
                    ft.Column(
                        [
                            ft.Text("Modules", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300),
                            ft.Container(height=1, bgcolor=ft.Colors.GREY_800),
                            ft.Row(
                                [
                                    ft.Text("Loaded Modules", size=13, color=ft.Colors.GREY_400, expand=True),
                                    ft.Text(str(len(state.modules.classes)), size=13, color=CYAN),
                                ],
                            ),
                            ft.Row(
                                [
                                    ft.Text("Enabled Modules", size=13, color=ft.Colors.GREY_400, expand=True),
                                    ft.Text(str(len(state.get_enabled_modules())), size=13, color=CYAN),
                                ],
                            ),
                        ],
                        spacing=10,
                    ),
                    bgcolor=ft.Colors.GREY_900,
                    border_radius=12,
                    padding=16,
                ),
                ft.Container(
                    ft.Column(
                        [
                            ft.Text("Targets", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300),
                            ft.Container(height=1, bgcolor=ft.Colors.GREY_800),
                            ft.Row(
                                [
                                    ft.Text("Total Targets", size=13, color=ft.Colors.GREY_400, expand=True),
                                    ft.Text(str(len(state.targets)), size=13, color=CYAN),
                                ],
                            ),
                            ft.Row(
                                [
                                    ft.Text("Selected Targets", size=13, color=ft.Colors.GREY_400, expand=True),
                                    ft.Text(str(len(state.get_selected_targets())), size=13, color=CYAN),
                                ],
                            ),
                        ],
                        spacing=10,
                    ),
                    bgcolor=ft.Colors.GREY_900,
                    border_radius=12,
                    padding=16,
                ),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        padding=24,
    )

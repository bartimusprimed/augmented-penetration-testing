import flet as ft
import logging
from typing import Callable, cast
from dataclasses import dataclass, field
from ipaddress import IPv4Address
from models.target import Target
from models.apt import Apt
from components.targets.add import add_target


@ft.component
def target(t: Target, state: Apt):
    def show_target_details(e: ft.Event[ft.Button]):
        selected_target = state.get_target(target_ip.value)
        ft.context.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(f"Log for {t.ip_label}"),
                alignment=ft.Alignment.CENTER,
                icon=ft.Icon(ft.Icons.INFO_OUTLINED),
                content=ft.Column([
                    ft.ListView([
                        ft.Text(entry) for entry in t.activity_log
                    ]),
                    ft.Button("Delete Target", on_click=lambda e: state.remove_target(
                        selected_target))
                ])
            )
        )

    def update_target_field_and_notify(e: ft.Event[ft.Checkbox]):
        t.update_field("is_selected", e.control.value)
        state.trigger_update()

    target_ip = ft.Text(t.ip_label, weight=ft.FontWeight.BOLD, size=24)
    target_status = ft.Text(
        t.current_status, expand=True, expand_loose=True, no_wrap=False)
    return ft.Container(
        ft.Card(
            ft.Column(
                [
                    ft.Row(
                        [ft.Checkbox("Selected", t.is_selected, on_change=update_target_field_and_notify, label_position=ft.LabelPosition.RIGHT)], alignment=ft.MainAxisAlignment.CENTER),
                    target_ip,
                    ft.Row([
                        ft.Text("Status:"),
                        target_status,
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Button("Target Details", data=t.ip_label,
                              on_click=show_target_details, elevation=5, bgcolor=ft.Colors.BLUE_GREY)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ), elevation=3, bgcolor=t.color_status
        ), alignment=ft.Alignment.CENTER, expand=True
    )

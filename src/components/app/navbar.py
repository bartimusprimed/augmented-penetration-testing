from typing import Callable
import flet as ft


def NavBar(function_to_call: Callable) -> ft.NavigationBar:
    navbar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(ft.Icons.HOME_OUTLINED, "Home"),
            ft.NavigationBarDestination(ft.Icons.COMPUTER_OUTLINED, "Targets"),
            ft.NavigationBarDestination(
                ft.Icons.VIEW_MODULE_OUTLINED, "Modules"),
            ft.NavigationBarDestination(
                ft.Icons.SETTINGS_APPLICATIONS_OUTLINED, "Settings"),
        ], on_change=lambda e: function_to_call(navbar.selected_index))
    return navbar


import flet as ft
from ipaddress import IPv4Network
from typing import cast
from dataclasses import dataclass, field
from pathlib import Path
from utils.module_loader import ModuleLoader
from models.target import Target, create_target


@ft.observable
@dataclass
class Apt:
    targets: list[Target] = field(default_factory=list)
    modules: ModuleLoader = ModuleLoader()
    version: str = "0.0.1 (Alpha)"
    title: str = "APT"
    description: str = "Augmented Penetration Testing"

    def trigger_update(self):
        cast(ft.Observable, self).notify()

    def remove_target(self, t: Target):
        ft.context.page.show_dialog(ft.AlertDialog(
            title="Please Wait", content=ft.Row([
                ft.Text("Removing Target")])))
        self.targets.remove(t)
        ft.context.page.pop_dialog()
        ft.context.page.pop_dialog()

    def create_new_target(self, ip: str) -> Target:
        target = create_target(ip)
        self.targets.append(target)
        return target

    def get_target(self, t: Target | str) -> Target:
        selected_target = []
        if isinstance(t, Target):
            selected_target = [
                target for target in self.targets if t == target]
        if isinstance(t, str):
            selected_target = [
                target for target in self.targets if t == target.ip_label]
        return selected_target[0]

    def create_sample_targets(self, count):
        if count > 255:
            count = 255
        for i in range(1, count):
            self.create_new_target(f"129.239.33.{i}")

    def get_enabled_modules(self):
        return [mod_name for mod_name, mod_value in self.modules.classes.items() if mod_value.enabled]

    def get_selected_targets(self):
        return [selected for selected in self.targets if selected.is_selected]

    async def select_all_targets(self):
        ft.context.page.show_dialog(ft.AlertDialog(
            title="Please Wait", content=ft.Row([
                ft.Text("Selecting all targets")])))
        if len(self.get_selected_targets()) < len(self.targets) / 2:
            for t in self.targets:
                t.is_selected = True
        else:
            for t in self.targets:
                t.is_selected = False
        self.trigger_update()
        ft.context.page.pop_dialog()

    async def create_new_target_range(self, ip_range: str):
        ft.context.page.show_dialog(ft.AlertDialog(title="Please Wait", content=ft.Row([
            ft.Text("Adding range of IPs")])))
        ip_network = IPv4Network(ip_range)
        for ip in ip_network:
            self.create_new_target(str(ip))
        self.trigger_update()
        ft.context.page.pop_dialog()

    async def enable_module(self, e: ft.Event[ft.Checkbox]):
        get_class = self.modules.classes.get(str(e.control.label))
        if get_class is not None:
            get_class.enable(e.control.value)

    async def run_action(self, e: ft.Event[ft.Button]):
        get_class = self.modules.classes.get(str(e.control.data))
        if get_class is not None:
            get_class.is_running = True
            for t in self.get_selected_targets():
                t.update_field("current_status", "Running...")
                e.page.run_thread(get_class.run, t)  # type: ignore
            get_class.is_running = False

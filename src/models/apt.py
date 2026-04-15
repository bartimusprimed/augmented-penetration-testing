
import flet as ft
from ipaddress import IPv4Network
from typing import cast
from dataclasses import dataclass, field
from pathlib import Path
from utils.module_loader import ModuleLoader
from models.target import Target, create_target, MESSAGE_TYPE
from models.chain import Chain


@ft.observable
@dataclass
class Apt:
    targets: list[Target] = field(default_factory=list)
    modules: ModuleLoader = ModuleLoader()
    chains: list[Chain] = field(default_factory=list)
    version: str = "0.0.1 (Alpha)"
    title: str = "APT"
    description: str = "Augmented Penetration Testing"
    local_target: Target | None = None

    def trigger_update(self):
        cast(ft.Observable, self).notify()

    def start_local_beacon(self) -> None:
        """Create a localhost target and start the default C2 beacon on it.

        Detects the local OS immediately via ``platform.system()`` and stores
        it on the target so the UI can display it before the beacon even
        checks in.  The blocking ``beacon.run()`` call is scheduled on a
        background thread via ``ft.context.page.run_thread`` so the UI stays
        responsive.

        Must be called from a Flet-managed context (e.g. an ``on_mounted``
        handler) so that ``ft.context.page`` is available.
        """
        import platform as _platform

        if self.local_target is not None:
            return

        beacon_mod = self.modules.classes.get("beacon")
        if beacon_mod is None:
            return

        local = self.create_new_target("127.0.0.1")
        local.os_guess = _platform.system()
        local.log_activity(
            f"Local OS detected: {local.os_guess}", True, MESSAGE_TYPE.INFORMATION
        )
        self.local_target = local
        self.trigger_update()
        ft.context.page.run_thread(beacon_mod.run, local)

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

    def create_chain(self, name: str = "New Chain") -> Chain:
        chain = Chain(name=name)
        self.chains.append(chain)
        self.trigger_update()
        return chain

    def remove_chain(self, chain: Chain):
        if chain in self.chains:
            self.chains.remove(chain)
            self.trigger_update()

    async def run_chain(self, chain: Chain, e: ft.Event):
        selected = self.get_selected_targets()
        if not selected:
            ft.context.page.show_dialog(ft.AlertDialog(
                title=ft.Text("No Targets Selected"),
                icon=ft.Icon(ft.Icons.WARNING_OUTLINED),
            ))
            return

        confirmed: list[bool] = [False]
        confirmed_event = __import__("threading").Event()

        target_labels = ft.Column(
            [ft.Text(f"  • {t.ip_label}", size=13) for t in selected],
            spacing=4,
        )

        def _confirm(_):
            confirmed[0] = True
            confirmed_event.set()
            ft.context.page.pop_dialog()

        def _cancel(_):
            confirmed_event.set()
            ft.context.page.pop_dialog()

        ft.context.page.show_dialog(ft.AlertDialog(
            icon=ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER_400, size=36),
            title=ft.Text("Run Chain?"),
            content=ft.Column(
                [
                    ft.Text(
                        f"You are about to run \"{chain.name}\" against {len(selected)} "
                        f"target{'s' if len(selected) != 1 else ''}:",
                        size=13,
                    ),
                    target_labels,
                    ft.Text(
                        "This could be destructive. Make sure you have authorization.",
                        size=12,
                        color=ft.Colors.AMBER_400,
                        italic=True,
                    ),
                ],
                spacing=8,
                tight=True,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=_cancel),
                ft.TextButton(
                    "Run Chain",
                    on_click=_confirm,
                    style=ft.ButtonStyle(color=ft.Colors.RED_400),
                ),
            ],
        ))

        confirmed_event.wait(timeout=300)
        if not confirmed[0]:
            return

        def execute_chain():
            import concurrent.futures
            chain.is_running = True
            chain.target_count = len(selected)
            chain.trigger_update()
            try:
                topo_order = chain._topo_order()
                total_steps = len(topo_order)
                for step_idx, node_id in enumerate(topo_order):
                    node = chain.nodes.get(node_id)
                    if node is None:
                        continue
                    mod = self.modules.classes.get(node.module_key)
                    if mod is None:
                        node.status = "skipped"
                        chain.trigger_update()
                        continue

                    node.status = "running"
                    chain.current_step = step_idx + 1
                    chain.trigger_update()

                    step_label = f"Chain step {step_idx + 1}/{total_steps}: {mod.name or node.module_key}..."
                    for t in selected:
                        t.update_field("current_status", step_label)

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = {executor.submit(mod.run, t): t for t in selected}
                        concurrent.futures.wait(futures)

                    node.status = "success"
                    chain.trigger_update()
            finally:
                chain.is_running = False
                chain.current_step = 0
                chain.trigger_update()

        e.page.run_thread(execute_chain)

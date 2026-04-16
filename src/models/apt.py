
import flet as ft
import json
import logging
import time
import uuid
from ipaddress import IPv4Network
from typing import cast
from dataclasses import dataclass, field
from pathlib import Path
from utils.module_loader import ModuleLoader
from models.target import Target, create_target, MESSAGE_TYPE
from models.chain import Chain
from models.chain_node import ChainNode


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
    chains_save_status: str = "Saved"
    chains_last_saved_at: float = 0.0
    _chains_file: Path = field(init=False, repr=False)

    def __post_init__(self):
        self._chains_file = Path(__file__).resolve().parents[2] / ".apt" / "chains.json"
        self.load_chains()

    def trigger_update(self):
        cast(ft.Observable, self).notify()

    def _bind_chain(self, chain: Chain) -> None:
        chain.on_change = self.save_chains

    def save_chains(self) -> None:
        """Persist chain definitions to disk."""
        payload: list[dict] = []
        for chain in self.chains:
            payload.append(
                {
                    "name": chain.name,
                    "nodes": [
                        {
                            "node_id": node.node_id,
                            "module_key": node.module_key,
                            "position": [node.position[0], node.position[1]],
                            "status": node.status,
                        }
                        for node in chain.nodes.values()
                    ],
                    "edges": [[src, dst] for src, dst in chain.edges],
                }
            )

        try:
            self._chains_file.parent.mkdir(parents=True, exist_ok=True)
            self._chains_file.write_text(json.dumps(payload, indent=2))
            self.chains_save_status = "Saved"
            self.chains_last_saved_at = time.time()
            self.trigger_update()
        except OSError as exc:
            logging.warning("Unable to save chains: %s", exc)
            self.chains_save_status = "Save failed"
            self.trigger_update()

    def load_chains(self) -> None:
        """Load persisted chain definitions from disk."""
        self.chains = []
        if not self._chains_file.exists():
            return

        try:
            raw = json.loads(self._chains_file.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            logging.warning("Unable to load chains: %s", exc)
            return

        if not isinstance(raw, list):
            return

        for item in raw:
            if not isinstance(item, dict):
                continue

            chain = Chain(name=str(item.get("name", "New Chain")))
            nodes = item.get("nodes", [])
            if isinstance(nodes, list):
                for node_data in nodes:
                    if not isinstance(node_data, dict):
                        continue
                    position = node_data.get("position", [0.0, 0.0])
                    if not isinstance(position, list) or len(position) != 2:
                        position = [0.0, 0.0]
                    node = ChainNode(
                        module_key=str(node_data.get("module_key", "")),
                        node_id=str(node_data.get("node_id", "")) or str(uuid.uuid4())[:8],
                        position=(float(position[0]), float(position[1])),
                        status=str(node_data.get("status", "pending")),
                    )
                    chain.nodes[node.node_id] = node

            edges = item.get("edges", [])
            if isinstance(edges, list):
                for edge in edges:
                    if isinstance(edge, list) and len(edge) == 2:
                        chain.edges.append((str(edge[0]), str(edge[1])))

            chain.is_running = False
            chain.current_step = 0
            chain.target_count = 0
            self._bind_chain(chain)
            self.chains.append(chain)

        self.chains_last_saved_at = time.time()
        self.chains_save_status = "Loaded"

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
        local.update_field("os_guess", _platform.system())
        local.log_activity(
            f"Local OS detected: {local.os_guess}", True, MESSAGE_TYPE.INFORMATION
        )
        self.local_target = local
        self.trigger_update()
        ft.context.page.run_thread(beacon_mod.run, local)

    def stop_local_beacon(self) -> None:
        """Terminate the local beacon subprocess and stop the C2 server.

        Called on app shutdown; safe to call even if the beacon was never
        started.  Does not require a Flet renderer context.
        """
        if self.local_target is None:
            return
        beacon_mod = self.modules.classes.get("beacon")
        if beacon_mod is not None:
            beacon_mod.shutdown(self.local_target)
        self.local_target = None

    def shutdown(self) -> None:
        """Best-effort teardown for app shutdown.

        Stops all running beacon subprocesses/server instances and clears
        local beacon tracking state.
        """
        beacon_mod = self.modules.classes.get("beacon")
        if beacon_mod is not None and hasattr(beacon_mod, "shutdown_all"):
            beacon_mod.shutdown_all()

        for target in self.targets:
            target.update_field("beacon_connected", False)
            target.update_field("beacon_pid", 0)

        self.local_target = None

    def kill_all_local_beacons(self) -> int:
        """Kill all locally spawned beacon processes and reset target C2 state.

        Returns the number of targets that were marked as having an active
        local beacon before the reset.
        """
        active_count = 0
        for target in self.targets:
            if target.beacon_pid != 0 or target.beacon_connected:
                active_count += 1

        beacon_mod = self.modules.classes.get("beacon")
        if beacon_mod is not None and hasattr(beacon_mod, "shutdown_all"):
            beacon_mod.shutdown_all()

        for target in self.targets:
            if target.beacon_pid != 0 or target.beacon_connected:
                target.log_activity(
                    "Local beacon terminated by operator",
                    True,
                    MESSAGE_TYPE.INFORMATION,
                )
            target.update_field("beacon_connected", False)
            target.update_field("beacon_pid", 0)
            target.update_field("beacon_session_id", "")

        self.local_target = None
        self.trigger_update()
        return active_count

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
        self._bind_chain(chain)
        self.chains.append(chain)
        self.save_chains()
        self.trigger_update()
        return chain

    def remove_chain(self, chain: Chain):
        if chain in self.chains:
            self.chains.remove(chain)
            self.save_chains()
            self.trigger_update()

    async def run_chain(self, chain: Chain, e: ft.Event):
        selected = self.get_selected_targets()
        if not selected:
            ft.context.page.show_dialog(ft.AlertDialog(
                title=ft.Text("No Targets Selected"),
                icon=ft.Icon(ft.Icons.WARNING_OUTLINED),
            ))
            return

        target_labels = ft.Column(
            [ft.Text(f"  • {t.ip_label}", size=13) for t in selected],
            spacing=4,
        )

        def execute_chain():
            chain.is_running = True
            chain.target_count = len(selected)
            chain.trigger_update()
            for t in selected:
                t.log_activity(
                    f"---Start CHAIN '{chain.name}' ({len(chain._topo_order())} steps)---",
                    True,
                    MESSAGE_TYPE.INFORMATION,
                )
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

                    failures = 0
                    for target in selected:
                        try:
                            mod.run(target)
                        except Exception as exc:
                            failures += 1
                            target.log_activity(
                                f"Chain step {step_idx + 1}/{total_steps} failed in {mod.name or node.module_key}: {exc}",
                                True,
                                MESSAGE_TYPE.ERROR,
                            )
                        else:
                            target.log_activity(
                                f"Chain step {step_idx + 1}/{total_steps} completed: {mod.name or node.module_key}",
                                True,
                                MESSAGE_TYPE.SUCCESS,
                            )

                    node.status = "failed" if failures > 0 else "success"
                    chain.trigger_update()
            finally:
                chain.is_running = False
                chain.current_step = 0
                chain.trigger_update()
                for t in selected:
                    t.log_activity(
                        f"---Finish CHAIN '{chain.name}'---",
                        True,
                        MESSAGE_TYPE.INFORMATION,
                    )

        def _confirm(_):
            ft.context.page.pop_dialog()
            e.page.run_thread(execute_chain)

        def _cancel(_):
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

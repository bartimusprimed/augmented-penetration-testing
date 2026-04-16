import sys
import logging
import flet as ft
from abc import ABC, abstractmethod
from models.target import Target, MESSAGE_TYPE
from models.module_metadata import AttackTactic, TargetOS, TargetArch


@ft.observable
class APT_MODULE(ABC):
    is_running: bool = False
    enabled: bool = True
    current_status: str = "None"
    name: str = ""
    description: str = ""
    tactic: AttackTactic = AttackTactic.RECONNAISSANCE
    technique_id: str = ""
    technique_name: str = ""
    # Subclasses should override these class-level attributes with new list
    # instances to avoid sharing the base-class defaults across sibling classes.
    compatible_os: list[TargetOS] = [TargetOS.ANY]
    compatible_arch: list[TargetArch] = [TargetArch.ANY]
    # Variables system: declare what this module needs before running and
    # what it writes for downstream modules.
    consumes_variables: list[str] = []
    produces_variables: list[str] = []

    def __init__(self) -> None:
        super().__init__()
        if not self.name:
            self.name = self.__class__.__name__

    def _normalize_target_os(self, target: Target) -> str:
        raw = str(target.get_variable("target.os", target.os_guess) or "").strip().lower()
        if "windows" in raw:
            return "windows"
        if "linux" in raw:
            return "linux"
        if "mac" in raw or "darwin" in raw or "os x" in raw:
            return "mac"
        return "other"

    def render_template(self, target: Target, template: str, extra: dict | None = None) -> str:
        return target.format_string(template, extra)

    def run(self, target: Target):
        target.start_work()
        target.log_activity(
            f"---Start {self.__class__.__name__.upper()} Module---")
        success = True
        try:
            missing = [k for k in self.consumes_variables if not target.has_variable(k)]
            if missing:
                success = False
                target.log_activity(
                    f"Missing required variables: {', '.join(missing)}",
                    True,
                    MESSAGE_TYPE.ERROR,
                )
            else:
                target_os = self._normalize_target_os(target)
                match target_os:
                    case "windows":
                        self.run_windows(target)
                    case "linux":
                        self.run_linux(target)
                    case "mac":
                        self.run_mac(target)
                    case _:
                        self.run_other(target_os, target)
        except PermissionError as exc:
            success = False
            if sys.platform == "darwin":
                msg = (
                    "Permission denied – raw packet operations require BPF device "
                    "access on macOS. Do NOT run APT with sudo (macOS blocks GUI apps "
                    "as root). Grant BPF access once:\n"
                    "  sudo dseditgroup -o edit -a \"$USER\" -t user access_bpf\n"
                    "Log out and back in, then restart APT."
                )
            else:
                msg = (
                    "Permission denied – raw socket access requires elevated "
                    "privileges. On Linux: grant cap_net_raw to the Python executable "
                    "(sudo setcap cap_net_raw+eip <path/to/python>), or run with sudo. "
                    "Use 'which python3' or check sys.executable for the correct path."
                )
            logging.log(logging.ERROR, f"{self.__class__.__name__}: {exc}")
            target.log_activity(msg, True, MESSAGE_TYPE.ERROR)
        if success:
            for key in self.produces_variables:
                if not target.has_variable(key):
                    target.set_variable(key, True)
        target.log_activity(
            f"---Finish {self.__class__.__name__.upper()} Module---")
        target.finish_work()

    def run_windows(self, target: Target):
        self.action(target)

    def run_mac(self, target: Target):
        self.action(target)

    def run_linux(self, target: Target):
        self.action(target)

    def run_other(self, os_name: str, target: Target):
        target.log_activity(
            f"Unknown target OS '{os_name}', running generic module path.",
            True,
            MESSAGE_TYPE.INFORMATION,
        )
        self.action(target)

    def action(self, target: Target):
        ...

    def enable(self, e):
        ...

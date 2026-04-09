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

    def __init__(self) -> None:
        super().__init__()
        if not self.name:
            self.name = self.__class__.__name__

    def run(self, target: Target):
        target.start_work()
        target.log_activity(
            f"---Start {self.__class__.__name__.upper()} Module---")
        try:
            self.action(target)
        except PermissionError as exc:
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
        target.log_activity(
            f"---Finish {self.__class__.__name__.upper()} Module---")
        target.finish_work()

    @abstractmethod
    def action(self, target: Target):
        ...

    @abstractmethod
    def enable(self, e):
        ...

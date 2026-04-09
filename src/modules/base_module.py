import flet as ft
from abc import ABC, abstractmethod
from models.target import Target
from models.module_metadata import AttackTactic, TargetOS, TargetArch


@ft.observable
class APT_MODULE(ABC):
    is_running: bool = False
    enabled: bool = False
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
        self.action(target)
        target.log_activity(
            f"---Finish {self.__class__.__name__.upper()} Module---")
        target.finish_work()

    @abstractmethod
    def action(self, target: Target):
        ...

    @abstractmethod
    def enable(self, e):
        ...

import flet as ft
import logging
import enum
from typing import Callable, cast
from dataclasses import dataclass, field
from ipaddress import IPv4Address


class MESSAGE_TYPE(enum.Enum):
    SUCCESS = 0
    ERROR = 1
    INFORMATION = 2


@ft.observable
class Target:
    is_selected: bool = False
    ip_label: str = ""
    is_alive: bool = False
    is_busy: bool = False
    current_status: str = "Idle"
    color_status: ft.Colors = ft.Colors(ft.Colors.GREY_900)
    # on_this_target_updated: Callable | None = None
    activity_log: list[str] = field(default_factory=list)
    ports: list[int] = field(default_factory=list)

    def update_field(self, field_name, field_value):
        try:
            getattr(self, field_name)
            setattr(self, field_name, field_value)
            logging.log(
                logging.DEBUG, f"Updating target attribute {field_name} with the value {field_value}")
        except:
            logging.log(logging.ERROR, "Could not set target attribute")

    def start_work(self):
        self.update_field("is_busy", True)

    def finish_work(self):
        self.update_field("is_busy", False)

    def log_activity(self, msg: str, is_status_update: bool = False, message_type: MESSAGE_TYPE = MESSAGE_TYPE.INFORMATION):
        if is_status_update:
            match(message_type):
                case MESSAGE_TYPE.ERROR:
                    self.color_status = ft.Colors.RED
                case MESSAGE_TYPE.SUCCESS:
                    self.color_status = ft.Colors.GREEN
                case _:
                    self.color_status = ft.Colors.AMBER
            self.current_status = msg
        self.activity_log.append(msg)


def create_target(ip: str) -> Target:
    t = Target()
    t.ip_label = ip
    t.activity_log = []
    t.ports = []
    t.log_activity(f"Target with {ip} Created")
    return t

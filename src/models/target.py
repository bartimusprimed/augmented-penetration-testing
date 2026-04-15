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
    os_guess: str = ""
    # C2 beacon fields
    beacon_session_id: str = ""
    beacon_last_seen: float = 0.0
    beacon_interval: int = 10
    beacon_connected: bool = False
    beacon_c2_port: int = 8443
    beacon_pid: int = 0
    beacon_shell_history: list[str] = field(default_factory=list)
    # Facts system: open-ended set of string keys produced by modules
    facts: set = field(default_factory=set)

    def update_field(self, field_name, field_value):
        try:
            getattr(self, field_name)
            setattr(self, field_name, field_value)
            logging.log(
                logging.DEBUG, f"Updating target attribute {field_name} with the value {field_value}")
        except Exception:
            logging.log(logging.ERROR, "Could not set target attribute")

    def set_fact(self, key: str) -> None:
        """Record that this target has the named fact (e.g. 'host_alive').

        Also keeps legacy boolean/list fields in sync for backward compatibility.
        """
        self.facts.add(key)
        cast(ft.Observable, self).notify()
        match key:
            case "host_alive":
                self.is_alive = True
            case "open_ports":
                pass  # ports list is updated separately
            case _:
                pass

    def has_fact(self, key: str) -> bool:
        """Return True if this target has the named fact."""
        return key in self.facts

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
    t.os_guess = ""
    t.beacon_shell_history = []
    t.facts = set()
    t.log_activity(f"Target with {ip} Created")
    return t

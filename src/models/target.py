import flet as ft
import logging
import enum
from typing import Any, cast
from dataclasses import dataclass, field


class MESSAGE_TYPE(enum.Enum):
    SUCCESS = 0
    ERROR = 1
    INFORMATION = 2


@dataclass
class ActivityResult:
    message: str
    message_type: MESSAGE_TYPE = MESSAGE_TYPE.INFORMATION
    is_status_update: bool = False
    timestamp: float = 0.0
    details: str = ""


@ft.observable
class Target:
    is_selected: bool = False
    ip_label: str = ""
    is_alive: bool = False
    is_busy: bool = False
    current_status: str = "Idle"
    color_status: ft.Colors = ft.Colors(ft.Colors.GREY_900)
    # on_this_target_updated: Callable | None = None
    activity_log: list[ActivityResult] = field(default_factory=list)
    ports: list[int] = field(default_factory=list)
    os_guess: str = ""
    # C2 beacon fields
    beacon_session_id: str = ""
    beacon_last_seen: float = 0.0
    beacon_interval: int = 10
    beacon_connected: bool = False
    beacon_c2_port: int = 8443
    beacon_pid: int = 0
    # Variables system: open-ended key/value store shared across modules/chains.
    variables: dict[str, Any] = field(default_factory=dict)

    def update_field(self, field_name, field_value):
        try:
            getattr(self, field_name)
            setattr(self, field_name, field_value)
            self._sync_default_variables()
            logging.log(
                logging.DEBUG, f"Updating target attribute {field_name} with the value {field_value}")
            cast(ft.Observable, self).notify()
        except Exception:
            logging.log(logging.ERROR, "Could not set target attribute")

    def _sync_default_variables(self) -> None:
        self.variables["target.ip"] = self.ip_label
        self.variables["target.os"] = self.os_guess
        self.variables["target.is_alive"] = self.is_alive
        self.variables["target.current_status"] = self.current_status

    def set_variable(self, key: str, value: Any) -> None:
        """Set or update a target variable by key.

        Variables can be consumed by subsequent modules and formatted into
        commands/payloads via Python format strings.
        """
        self.variables[key] = value
        cast(ft.Observable, self).notify()

    def set_variables(self, values: dict[str, Any]) -> None:
        self.variables.update(values)
        cast(ft.Observable, self).notify()

    def get_variable(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def has_variable(self, key: str) -> bool:
        return key in self.variables

    def format_string(self, template: str, extra: dict[str, Any] | None = None) -> str:
        """Format a template using target variables.

        Missing placeholders are left untouched so module writers can safely
        iterate on templates without immediate hard failures.
        """
        context: dict[str, Any] = dict(self.variables)
        if extra:
            context.update(extra)

        class _SafeDict(dict):
            def __missing__(self, key):
                return "{" + str(key) + "}"

        return template.format_map(_SafeDict(context))

    def start_work(self):
        self.update_field("is_busy", True)

    def finish_work(self):
        self.update_field("is_busy", False)

    def log_activity(
        self,
        msg: str,
        is_status_update: bool = False,
        message_type: MESSAGE_TYPE = MESSAGE_TYPE.INFORMATION,
        details: str = "",
    ):
        import time

        if is_status_update:
            match(message_type):
                case MESSAGE_TYPE.ERROR:
                    self.color_status = ft.Colors.RED
                case MESSAGE_TYPE.SUCCESS:
                    self.color_status = ft.Colors.GREEN
                case _:
                    self.color_status = ft.Colors.AMBER
            self.current_status = msg
        self.activity_log.append(
            ActivityResult(
                message=msg,
                message_type=message_type,
                is_status_update=is_status_update,
                timestamp=time.time(),
                details=details,
            )
        )
        cast(ft.Observable, self).notify()


def create_target(ip: str) -> Target:
    t = Target()
    t.ip_label = ip
    t.activity_log = []
    t.ports = []
    t.os_guess = ""
    t.variables = {}
    t._sync_default_variables()
    t.log_activity(f"Target with {ip} Created")
    return t

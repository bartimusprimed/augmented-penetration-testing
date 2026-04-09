import flet as ft
from typing import cast
from dataclasses import dataclass, field


@ft.observable
@dataclass
class Chain:
    name: str = "New Chain"
    module_keys: list[str] = field(default_factory=list)
    is_running: bool = False
    current_step: int = 0
    target_count: int = 0

    def trigger_update(self):
        cast(ft.Observable, self).notify()

    def add_module(self, key: str):
        if key not in self.module_keys:
            self.module_keys.append(key)
            self.trigger_update()

    def remove_module(self, key: str):
        if key in self.module_keys:
            self.module_keys.remove(key)
            self.trigger_update()

    def move_up(self, key: str):
        idx = self.module_keys.index(key)
        if idx > 0:
            self.module_keys[idx], self.module_keys[idx - 1] = (
                self.module_keys[idx - 1],
                self.module_keys[idx],
            )
            self.trigger_update()

    def move_down(self, key: str):
        idx = self.module_keys.index(key)
        if idx < len(self.module_keys) - 1:
            self.module_keys[idx], self.module_keys[idx + 1] = (
                self.module_keys[idx + 1],
                self.module_keys[idx],
            )
            self.trigger_update()

    def clear(self):
        self.module_keys = []
        self.trigger_update()

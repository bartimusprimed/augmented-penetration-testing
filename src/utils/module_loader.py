import importlib.util
import logging
import flet as ft
from pathlib import Path
from modules.base_module import APT_MODULE
from models.module_metadata import AttackTactic, TargetOS, TargetArch


@ft.observable
class ModuleLoader:

    module_directory = Path.joinpath(Path.cwd(), "modules")
    modules: dict[str, APT_MODULE] = {}
    classes: dict[str, APT_MODULE] = {}

    def __init__(self):
        self.get_modules()

    def get_modules(self):
        if not self.module_directory.exists():
            self.module_directory = Path.joinpath(Path.cwd(), "src/modules")
        # Load root-level modules and one level of tactic subdirectories
        for module_file in (*self.module_directory.glob("*.py"),
                            *self.module_directory.glob("*/*.py")):
            if module_file.stem not in ("base_module", "__init__"):
                self._import_module(module_file)

    def _import_module(self, file_path: Path):
        class_key = file_path.stem
        if class_key in self.classes:
            logging.log(logging.INFO, f"{class_key!r} already in modules")
            return self.classes.get(class_key)

        module_name = ".".join(
            file_path.relative_to(self.module_directory).with_suffix("").parts
        )
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load spec for {file_path}")

        module = importlib.util.module_from_spec(spec)
        self.modules[class_key] = module  # type: ignore
        spec.loader.exec_module(module)
        self.classes[class_key] = getattr(module, class_key)()
        logging.log(logging.INFO, f"{class_key!r} has been imported")
        return module

    def get_modules_by_tactic(self, tactic: AttackTactic) -> dict[str, APT_MODULE]:
        return {k: v for k, v in self.classes.items() if v.tactic == tactic}

    def get_tactics_in_use(self) -> list[AttackTactic]:
        used = {v.tactic for v in self.classes.values()}
        return [t for t in AttackTactic if t in used]

    def get_modules_filtered(
        self,
        tactic: AttackTactic | None = None,
        os_filter: TargetOS | None = None,
        arch_filter: TargetArch | None = None,
    ) -> dict[str, APT_MODULE]:
        result = {}
        for k, v in self.classes.items():
            if tactic is not None and v.tactic != tactic:
                continue
            if (os_filter is not None
                    and TargetOS.ANY not in v.compatible_os
                    and os_filter not in v.compatible_os):
                continue
            if (arch_filter is not None
                    and TargetArch.ANY not in v.compatible_arch
                    and arch_filter not in v.compatible_arch):
                continue
            result[k] = v
        return result

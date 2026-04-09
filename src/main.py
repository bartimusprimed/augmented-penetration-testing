import sys
import flet as ft
from views.app_view import App
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("flet_core").setLevel(logging.INFO)


def _patch_scapy_macos() -> None:
    """On macOS the ARP cache can grow beyond scapy's default max_list_count
    (4096), causing an import-time crash (MaximumItemsCount).  Disabling the
    limit at startup prevents all scapy-based modules from breaking.
    See: https://github.com/secdev/scapy/pull/4892
    """
    if sys.platform != "darwin":
        return
    try:
        import scapy.config  # type: ignore
        scapy.config.conf.max_list_count = 0
        logging.log(logging.DEBUG, "macOS detected: scapy conf.max_list_count set to 0")
    except Exception as exc:
        logging.log(logging.WARNING, f"Could not patch scapy max_list_count: {exc}")


def render_app(page: ft.Page):
    page.render(lambda: App())  # type: ignore


if __name__ == "__main__":
    _patch_scapy_macos()
    ft.run(render_app)

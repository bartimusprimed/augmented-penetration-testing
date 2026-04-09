import sys
import flet as ft
from views.app_view import App
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("flet_core").setLevel(logging.INFO)


def _patch_scapy_macos() -> None:
    """On macOS, Scapy parses large BPF/ARP/routing data that can exceed the
    default max_list_count (4096), raising MaximumItemsCount.

    IMPORTANT: do NOT use 0 here.  In Scapy 2.7.0 the check in
    PacketListField.getfield() is:

        if len(lst) > (self.max_count or conf.max_list_count):

    Because Python's `or` returns the first truthy value, `None or 0` evaluates
    to 0, making the condition `len(lst) > 0` — which is True for every non-empty
    packet list and crashes all scapy modules immediately.

    sys.maxsize is the correct sentinel: `None or sys.maxsize` = sys.maxsize,
    and `len(lst) > sys.maxsize` is never True in practice.

    See: https://github.com/secdev/scapy/pull/4892
    """
    if sys.platform != "darwin":
        return
    try:
        import scapy.config  # type: ignore
        scapy.config.conf.max_list_count = sys.maxsize
        logging.log(logging.DEBUG, "macOS detected: scapy conf.max_list_count set to sys.maxsize")
    except Exception as exc:
        logging.log(logging.WARNING, f"Could not patch scapy max_list_count: {exc}")


_patch_scapy_macos()


def render_app(page: ft.Page):
    page.render(lambda: App())  # type: ignore


if __name__ == "__main__":
    ft.run(render_app)

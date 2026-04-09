import flet as ft
from views.app_view import App
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("flet_core").setLevel(logging.INFO)


def render_app(page: ft.Page):
    page.render(lambda: App())  # type: ignore


if __name__ == "__main__":
    ft.run(render_app)

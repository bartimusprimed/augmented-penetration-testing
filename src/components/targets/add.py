import flet as ft
from models.apt import Apt


@ft.component
def add_target(state: Apt):
    new_ip, set_new_ip = ft.use_state("")

    async def add_target(e: ft.Event[ft.TextField]):
        if len(e.control.value.split(".")) != 4:
            ft.context.page.show_dialog(ft.AlertDialog(
                title=ft.Text("Invalid IP or Range"),
                alignment=ft.Alignment.CENTER,
                icon=ft.Icon(ft.Icons.ERROR_OUTLINED)
            ))
            return
        else:
            if "/" not in e.control.value:
                state.create_new_target(e.control.value)
            else:
                await state.create_new_target_range(e.control.value)
            set_new_ip("")
            await new_target_ip_field.focus()

    new_target_ip_field = ft.TextField(
        hint_text="IP or Range (Enter to Add)", value=new_ip, on_submit=add_target, autocorrect=False, autofocus=True)

    return ft.Row(
        [
            ft.Text(
                f"Number of Modules Enabled: {len(state.get_enabled_modules())}"),
            new_target_ip_field,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, expand=True
    )

import flet as ft


@ft.component
def Workflow():
    return ft.Container(
        ft.Column([
            ft.Text("Workflow:",
                    text_align=ft.TextAlign.JUSTIFY, size=20),
            ft.Text("1. Add targets and select them via the targets tab, ping the targets, port scan them.",
                    text_align=ft.TextAlign.JUSTIFY),
            ft.Text("2. Enable modules on the module page. Run the modules on the selected targets by clicking run selected modules",
                    text_align=ft.TextAlign.JUSTIFY),
            ft.Text("3. View the results of the modules on the associated result tab that will be created when finished running",
                    text_align=ft.TextAlign.JUSTIFY),
        ], alignment=ft.MainAxisAlignment.CENTER), alignment=ft.Alignment.BOTTOM_CENTER
    )

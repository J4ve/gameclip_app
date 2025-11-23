import flet as ft
from app.gui import MainWindow


def main(page: ft.Page):
    """Main application entry point"""
    # TODO: Initialize MainWindow
    # TODO: Call build() and add to page
    # TODO: Handle app lifecycle
    
    # Temporary placeholder
    window = MainWindow(page)
    page.add(
        window.build()
        )
    page.update()


ft.app(main)

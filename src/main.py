import flet as ft
from app.gui import MainWindow
from access_control.gui.auth_screen import LoginScreen
from access_control.session import session_manager


def main(page: ft.Page):
    """Main application entry point with authentication"""
    page.title = "📽️ Video Merger App"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    
    # Handle login completion and show main app
    def handle_login_complete(user_info, role):
        """Called after successful login - show main app"""
        # Set global session
        session_manager.login(user_info, role)
        
        # Clear page and show main window
        page.clean()
        window = MainWindow(page)
        page.add(window.build())
        page.update()
        
        # Show welcome message
        page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(f"Welcome, {user_info.get('email', 'Guest')}! Role: {role.name.title()}"),
                action="OK"
            )
        )
    
    # Show login screen first
    login_screen = LoginScreen(page, on_login_complete=handle_login_complete)
    page.add(login_screen.build())
    page.update()


ft.app(main)

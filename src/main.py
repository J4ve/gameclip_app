import flet as ft
from app.gui import MainWindow
from app.gui.login_screen import LoginScreen
from access_control.session import session_manager


def main(page: ft.Page):
    """Main application entry point with authentication"""
    page.title = "Video Merger App"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 950
    page.window_min_width = 800
    page.window_min_height = 600
    
    # Handle login completion and show main app
    def handle_login_complete(user_info, role):
        """Called after successful login - show main app"""
        print(f"Login complete: {user_info}, Role: {role.name}")
        
        # Set global session
        session_manager.login(user_info, role)
        print(f"Session set: {session_manager.is_logged_in}")
        
        # Clear page and show main window
        page.clean()
        print("Page cleaned")
        
        try:
            window = MainWindow(page)
            print("MainWindow created")
            
            main_layout = window.build()
            print("MainWindow layout built")
            
            page.controls = [main_layout]
            print("Layout set as sole control")
            
            page.update()
            print("Page updated")
            
            # Show welcome message
            snack_bar = ft.SnackBar(
                content=ft.Text(f"Welcome, {user_info.get('email', 'Guest')}! Role: {role.name.title()}"),
                action="OK"
            )
            snack_bar.open = True
            page.update()
        except Exception as e:
            print(f"Error creating main window: {e}")
            # Show error message
            page.add(ft.Text(f"Error: {str(e)}", color=ft.Colors.RED))
            page.update()
    
    # Show login screen first
    login_screen = LoginScreen(page, on_login_complete=handle_login_complete)
    page.controls = [login_screen.build()]
    page.update()


ft.app(main)

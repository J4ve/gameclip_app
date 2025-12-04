"""
Example integration of Firebase auth into existing Flet app
Shows how to add login and role-based UI to main window
"""

import flet as ft
from access_control.auth.firebase_auth import firebase_auth
from access_control.auth.user_session import user_session
from access_control.gui.login_screen import LoginScreen
from access_control.gui.role_ui import AdBanner, AdminPanel, DevLogsPanel, RoleBasedContainer

def main(page: ft.Page):
    """
    Example main app with Firebase auth integrated.
    Replace this with your actual app's main window.
    """
    
    page.title = "Video Merger App (with Firebase Auth)"
    page.theme_mode = ft.ThemeMode.DARK
    
    # Login screen
    login_screen = LoginScreen(page, on_login_success=handle_login_success)
    
    # Main app content (shown after login)
    main_content = ft.Column([
        ft.Text(f"Welcome, {user_session.email}", size=20),
        ft.Text(f"Role: {user_session.role}", size=14, color=ft.Colors.CYAN),
        
        # Ad banner (hidden for premium users)
        AdBanner(),
        
        # Premium-only feature
        RoleBasedContainer(
            content=ft.Container(
                content=ft.Text("Premium Feature: No Ads!", size=16),
                bgcolor=ft.Colors.AMBER,
                padding=10,
                border_radius=5
            ),
            required_roles=['premium', 'dev', 'admin']
        ),
        
        # Dev logs panel
        DevLogsPanel(),
        
        # Admin panel
        AdminPanel(on_role_change=handle_role_change),
        
        # Logout button
        ft.ElevatedButton("Logout", on_click=handle_logout)
    ], scroll=ft.ScrollMode.AUTO)
    
    def handle_login_success(id_token: str):
        """Called after successful login."""
        # Verify token and get user info
        user_info = firebase_auth.verify_token(id_token)
        if user_info:
            user_session.login(user_info, id_token)
            page.clean()
            page.add(main_content)
            page.update()
    
    def handle_logout(e):
        """Logout and return to login screen."""
        user_session.logout()
        page.clean()
        page.add(login_screen.build())
        page.update()
    
    def handle_role_change(uid: str, new_role: str):
        """Called when admin changes a user's role."""
        print(f"Role changed: {uid} -> {new_role}")
        # Optionally notify user to refresh their token
    
    # Show login screen if not logged in
    if not user_session.is_logged_in:
        page.add(login_screen.build())
    else:
        page.add(main_content)

if __name__ == "__main__":
    ft.app(target=main)

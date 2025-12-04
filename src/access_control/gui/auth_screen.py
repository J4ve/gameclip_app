"""
Login Screen - Initial authentication screen before main app
Allows users to login as guest or with Google authentication
"""

import flet as ft
from typing import Callable, Optional
from access_control.roles import RoleManager, RoleType
from access_control.auth.firebase_auth_mock import get_firebase_auth
import os


class LoginScreen:
    """Login screen with guest and Google login options"""
    
    def __init__(self, page: ft.Page, on_login_complete: Optional[Callable] = None):
        self.page = page
        self.on_login_complete = on_login_complete
        
        # Initialize Firebase auth (will be loaded when needed)
        self.firebase_auth = None
        
        # UI components
        self.email_field = None
        self.password_field = None
        self.login_button = None
        self.register_button = None
        self.guest_button = None
        self.loading_ring = None
        self.status_text = None
        
        # Login state
        self.is_logging_in = False
    
    def _initialize_firebase(self) -> bool:
        """Initialize Firebase auth if config exists"""
        try:
            self.firebase_auth = get_firebase_auth()
            return True
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")
            return False
    
    def build(self) -> ft.Container:
        """Build and return the login screen UI"""
        
        # App title
        title = ft.Text(
            "🎮 Video Merger App",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_400,
            text_align=ft.TextAlign.CENTER
        )
        
        subtitle = ft.Text(
            "Choose how you want to continue",
            size=16,
            color=ft.Colors.GREY_400,
            text_align=ft.TextAlign.CENTER
        )
        
        # Guest login section
        guest_section = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.PERSON, size=40, color=ft.Colors.GREY_400),
                ft.Text("Continue as Guest", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "• Limited to 5 merges per day\n• Videos have watermark\n• Ads enabled\n• No upload to YouTube",
                    size=12,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.ElevatedButton(
                    "Continue as Guest",
                    icon=ft.Icons.PERSON,
                    on_click=self._handle_guest_login,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREY_700,
                        color=ft.Colors.WHITE,
                        padding=ft.padding.symmetric(horizontal=20, vertical=10)
                    )
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_600),
            border_radius=10,
            bgcolor=ft.Colors.GREY_900
        )
        
        # Google login section
        self.email_field = ft.TextField(
            label="Email",
            prefix_icon=ft.Icons.EMAIL,
            width=300,
            bgcolor=ft.Colors.GREY_800,
            border_color=ft.Colors.GREY_600
        )
        
        self.password_field = ft.TextField(
            label="Password",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            width=300,
            bgcolor=ft.Colors.GREY_800,
            border_color=ft.Colors.GREY_600,
            on_submit=self._handle_google_login
        )
        
        self.login_button = ft.ElevatedButton(
            "Login with Google",
            icon=ft.Icons.LOGIN,
            on_click=self._handle_google_login,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(horizontal=20, vertical=10)
            ),
            width=200
        )
        
        self.register_button = ft.TextButton(
            "Create Account",
            on_click=self._handle_register,
            style=ft.ButtonStyle(color=ft.Colors.BLUE_400)
        )
        
        # Loading indicator
        self.loading_ring = ft.ProgressRing(visible=False, width=20, height=20)
        
        # Status text
        self.status_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.RED_400,
            text_align=ft.TextAlign.CENTER,
            visible=False
        )
        
        google_section = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOGIN, size=40, color=ft.Colors.BLUE_400),
                ft.Text("Login with Google", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "• Upload to YouTube\n• No watermark\n• Higher merge limits\n• Role-based features",
                    size=12,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Test Accounts:\n• admin@test.com / admin123\n• user@test.com / user123\n• premium@test.com / premium123",
                    size=10,
                    color=ft.Colors.CYAN_400,
                    text_align=ft.TextAlign.CENTER
                ),
                self.email_field,
                self.password_field,
                ft.Row([
                    self.loading_ring,
                    self.login_button
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                self.register_button,
                self.status_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_600),
            border_radius=10,
            bgcolor=ft.Colors.GREY_900
        )
        
        # Main layout
        main_content = ft.Column([
            title,
            subtitle,
            ft.Container(height=20),  # Spacer
            ft.Row([
                guest_section,
                ft.VerticalDivider(color=ft.Colors.GREY_600),
                google_section
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=30),
            ft.Container(height=20),  # Spacer
            ft.Text(
                "Note: Using mock authentication for development",
                size=10,
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        
        return ft.Container(
            content=main_content,
            alignment=ft.alignment.center,
            padding=40,
            expand=True
        )
    
    def _handle_guest_login(self, e):
        """Handle guest login - assign guest role and continue"""
        try:
            # Create guest role
            guest_role = RoleManager.create_role(RoleType.GUEST)
            
            # Set session info (mock user session for guest)
            user_info = {
                'email': 'guest@local',
                'uid': 'guest',
                'role': 'guest'
            }
            
            # Call login completion callback
            if self.on_login_complete:
                self.on_login_complete(user_info, guest_role)
            
        except Exception as ex:
            self._show_error(f"Guest login failed: {str(ex)}")
    
    def _handle_google_login(self, e):
        """Handle Google/Firebase login"""
        if self.is_logging_in:
            return
        
        email = self.email_field.value.strip()
        password = self.password_field.value.strip()
        
        if not email or not password:
            self._show_error("Please enter email and password")
            return
        
        # Initialize Firebase if needed
        if not self.firebase_auth:
            if not self._initialize_firebase():
                self._show_error("Firebase not configured. Please set up firebase_config.json")
                return
        
        self._set_loading(True)
        
        try:
            # Attempt login with Firebase
            user_info = self.firebase_auth.sign_in(email, password)
            
            if user_info:
                # Get user role from Firebase custom claims or Firestore
                role_name = user_info.get('role', 'normal')  # Default to normal
                role = RoleManager.create_role_by_name(role_name)
                
                # Call login completion callback
                if self.on_login_complete:
                    self.on_login_complete(user_info, role)
            else:
                self._show_error("Login failed. Please check your credentials.")
                
        except Exception as ex:
            self._show_error(f"Login error: {str(ex)}")
        
        finally:
            self._set_loading(False)
    
    def _handle_register(self, e):
        """Handle account registration"""
        email = self.email_field.value.strip()
        password = self.password_field.value.strip()
        
        if not email or not password:
            self._show_error("Please enter email and password")
            return
        
        if len(password) < 6:
            self._show_error("Password must be at least 6 characters")
            return
        
        # Initialize Firebase if needed
        if not self.firebase_auth:
            if not self._initialize_firebase():
                self._show_error("Firebase not configured. Please set up firebase_config.json")
                return
        
        self._set_loading(True)
        
        try:
            # Create account with Firebase
            user_info = self.firebase_auth.create_account(email, password)
            
            if user_info:
                # Assign normal role to new users
                role = RoleManager.create_role(RoleType.NORMAL)
                
                # Set role in Firebase custom claims
                self.firebase_auth.set_custom_claims(user_info['uid'], {'role': 'normal'})
                
                # Call login completion callback
                if self.on_login_complete:
                    user_info['role'] = 'normal'
                    self.on_login_complete(user_info, role)
            else:
                self._show_error("Account creation failed.")
                
        except Exception as ex:
            self._show_error(f"Registration error: {str(ex)}")
        
        finally:
            self._set_loading(False)
    
    def _set_loading(self, loading: bool):
        """Show/hide loading indicator"""
        self.is_logging_in = loading
        self.loading_ring.visible = loading
        self.login_button.disabled = loading
        self.register_button.disabled = loading
        
        if loading:
            self.login_button.text = "Logging in..."
            self._hide_error()
        else:
            self.login_button.text = "Login with Google"
        
        self.page.update()
    
    def _show_error(self, message: str):
        """Show error message"""
        self.status_text.value = message
        self.status_text.color = ft.Colors.RED_400
        self.status_text.visible = True
        self.page.update()
    
    def _show_success(self, message: str):
        """Show success message"""
        self.status_text.value = message
        self.status_text.color = ft.Colors.GREEN_400
        self.status_text.visible = True
        self.page.update()
    
    def _hide_error(self):
        """Hide error/status message"""
        self.status_text.visible = False
        self.page.update()
"""
Login Screen - Initial authentication screen before main app
Allows users to login as guest or with Google authentication
"""

import flet as ft
from typing import Callable, Optional
from access_control.roles import RoleManager, RoleType
import os


class LoginScreen:
    """Login screen with guest and Google login options"""
    
    def __init__(self, page: ft.Page, on_login_complete: Optional[Callable] = None):
        self.page = page
        self.on_login_complete = on_login_complete
        
        # Initialize Firebase auth (will be loaded when needed)
        self.firebase_auth = None
        
        # UI components
        self.google_login_button = None
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
            "📽️ Video Merger App",
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
        
        # Google login section - OAuth button only
        self.google_login_button = ft.ElevatedButton(
            "Sign in with Google",
            icon=ft.Icons.LOGIN,
            on_click=self._handle_google_login,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(horizontal=30, vertical=15)
            ),
            width=250,
            height=50
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
                    "Click below to authenticate with your Google account\nin your default browser (same as YouTube upload)",
                    size=10,
                    color=ft.Colors.CYAN_400,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Row([
                    self.loading_ring,
                    self.google_login_button
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                self.status_text,
                self._build_previous_user_section()  # Add previous user section
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
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
                "Note: Google login uses YouTube OAuth (same as upload authentication)",
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
            print("Guest login started")
            
            # Create guest role
            guest_role = RoleManager.create_role(RoleType.GUEST)
            print(f"Guest role created: {guest_role.name}")
            
            # Set session info (mock user session for guest)
            user_info = {
                'email': 'guest@local',
                'uid': 'guest',
                'role': 'guest'
            }
            print(f"User info prepared: {user_info}")
            
            # Call login completion callback
            if self.on_login_complete:
                print("Calling login completion callback")
                self.on_login_complete(user_info, guest_role)
            else:
                print("No login completion callback set!")
            
        except Exception as ex:
            print(f"Guest login exception: {ex}")
            self._show_error(f"Guest login failed: {str(ex)}")
    
    def _handle_google_login(self, e):
        """Handle Google OAuth login - clears tokens first for fresh authentication"""
        if self.is_logging_in:
            return
        
        self._set_loading(True)
        self._show_status("Clearing previous tokens...")
        
        # Clear tokens first to force fresh authentication
        from access_control.session import session_manager
        session_manager._clear_oauth_tokens()
        
        try:
            # Use the actual YouTube uploader authentication
            from uploader.auth import get_youtube_service
            
            self._show_status("Opening browser for Google authentication...")
            
            # Get YouTube service - this will handle the real OAuth flow
            youtube_service = get_youtube_service()
            
            if not youtube_service or not youtube_service.credentials:
                self._show_error("Google authentication failed")
                return
            
            # Get user info from Google's UserInfo API
            self._show_status("Getting user information...")
            
            try:
                # Build userinfo service to get user details
                from googleapiclient.discovery import build
                userinfo_service = build('oauth2', 'v2', credentials=youtube_service.credentials)
                user_info_response = userinfo_service.userinfo().get().execute()
                
                # Extract user data from Google's response
                user_data = {
                    "email": user_info_response.get('email', 'unknown@gmail.com'),
                    "name": user_info_response.get('name', 'Google User'),
                    "given_name": user_info_response.get('given_name', ''),
                    "family_name": user_info_response.get('family_name', ''),
                    "picture": user_info_response.get('picture', ''),
                    "role": "normal",  # Default role for OAuth users
                    "provider": "google",
                    "authenticated": True,
                    "google_id": user_info_response.get('id', '')
                }
                
            except Exception as userinfo_ex:
                print(f"Could not get user info: {userinfo_ex}")
                # Fallback if userinfo API fails
                user_data = {
                    "email": "authenticated@gmail.com",
                    "name": "Google User",
                    "role": "normal",
                    "provider": "google", 
                    "authenticated": True
                }
            
            # Create role object
            role = RoleManager.create_role_by_name(user_data["role"])
            
            # Authenticate with session manager - this saves the session
            session_manager.login(user_data, role)
            
            self._show_status("Authentication successful!")
            
            # Call login completion callback
            if self.on_login_complete:
                self.on_login_complete(user_data, role)
            else:
                self._show_error("No login completion callback set!")
                
        except Exception as ex:
            print(f"OAuth error: {ex}")
            self._show_error(f"Authentication failed: {str(ex)}")
            
        finally:
            self._set_loading(False)
    
    def _set_loading(self, loading: bool):
        """Show/hide loading indicator"""
        self.is_logging_in = loading
        self.loading_ring.visible = loading
        self.google_login_button.disabled = loading
        
        if loading:
            self.google_login_button.text = "Authenticating..."
            self._hide_error()
        else:
            self.google_login_button.text = "Sign in with Google"
        
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
    
    def _show_status(self, message: str):
        """Show status message"""
        self.status_text.value = message
        self.status_text.color = ft.Colors.BLUE_400
        self.status_text.visible = True
        self.page.update()
    
    def _hide_error(self):
        """Hide error/status message"""
        self.status_text.visible = False
        self.page.update()
    
    def _build_previous_user_section(self):
        """Build section to login as previous user if available"""
        from access_control.session import session_manager
        
        if not session_manager.has_previous_user():
            return ft.Container()  # Empty container if no previous user
            
        last_user = session_manager.last_user
        user_display = last_user.get('name') or last_user.get('email', 'Previous User')
        
        previous_user_button = ft.TextButton(
            f"Login as {user_display}",
            icon=ft.Icons.PERSON_OUTLINE,
            on_click=self._handle_previous_user_login,
            style=ft.ButtonStyle(
                color=ft.Colors.GREEN_400,
                padding=ft.padding.symmetric(horizontal=10, vertical=5)
            )
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Divider(color=ft.Colors.GREY_600),
                ft.Text("Quick Login", size=12, color=ft.Colors.GREY_400),
                previous_user_button
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            margin=ft.margin.only(top=10)
        )
    
    def _handle_previous_user_login(self, e):
        """Handle login as previous user"""
        from access_control.session import session_manager
        
        if not session_manager.has_previous_user():
            self._show_error("No previous user available")
            return
            
        last_user = session_manager.last_user
        
        try:
            # Create role based on stored user data
            role = RoleManager.create_role_by_name(last_user.get('role', 'normal'))
            
            # Call login completion callback
            if self.on_login_complete:
                self.on_login_complete(last_user, role)
            else:
                self._show_error("No login completion callback set!")
                
        except Exception as ex:
            print(f"Previous user login error: {ex}")
            self._show_error(f"Failed to login as previous user: {str(ex)}")
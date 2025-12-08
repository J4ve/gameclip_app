"""
Login Screen with Firebase Integration
Allows users to login as guest or with Google authentication using Firebase
"""

import flet as ft
from typing import Callable, Optional
from access_control.roles import RoleManager, RoleType
import os


class LoginScreen:
    """Login screen with guest and Google login options and Firebase integration"""
    
    def __init__(self, page: ft.Page, on_login_complete: Optional[Callable] = None):
        self.page = page
        self.on_login_complete = on_login_complete
        
        # UI components
        self.google_login_button = None
        self.guest_button = None
        self.google_loading_ring = None
        self.guest_loading_ring = None
        self.status_text = None
        self.retry_button = None
        
        # Login state
        self.is_logging_in = False
        self.is_guest_logging_in = False
    
    def build(self) -> ft.Container:
        """Build and return the login screen UI"""
        # App title
        title = ft.Text(
            "📽️ Video Merger App",
            size=36,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_400,
            text_align=ft.TextAlign.CENTER
        )
        
        subtitle = ft.Text(
            "Merge, edit, and upload your videos seamlessly",
            size=14,
            color=ft.Colors.GREY_400,
            text_align=ft.TextAlign.CENTER
        )
        
        # Google login button
        self.google_login_button = ft.ElevatedButton(
            "Sign in with Google",
            icon=ft.Icons.LOGIN,
            on_click=self._handle_google_login,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.LIGHT_BLUE_700, ft.ControlState.HOVERED: ft.Colors.LIGHT_BLUE_600},
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(horizontal=40, vertical=18)
            ),
            width=300,
            height=55
        )
        
        # Google loading indicator
        self.google_loading_ring = ft.ProgressRing(visible=False, width=20, height=20)
        
        # Guest loading indicator
        self.guest_loading_ring = ft.ProgressRing(visible=False, width=16, height=16)
        
        # Guest text button
        self.guest_button = ft.TextButton(
            "Or continue without signing in",
            on_click=self._handle_guest_login,
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_400,
                padding=ft.padding.symmetric(horizontal=20, vertical=10)
            )
        )
        
        # Status text
        self.status_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.RED_400,
            text_align=ft.TextAlign.CENTER,
            visible=False
        )
        
        # Retry button for browser issues
        self.retry_button = ft.TextButton(
            "Browser didn't open? Click here to retry",
            icon=ft.Icons.REFRESH,
            on_click=self._handle_retry_auth,
            style=ft.ButtonStyle(
                color=ft.Colors.ORANGE_400,
                padding=ft.padding.symmetric(horizontal=15, vertical=8)
            ),
            visible=False
        )
        
        # Main login container
        login_card = ft.Container(
            content=ft.Column([
                ft.Text("Welcome", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                ft.Text(
                    "Sign in to upload to YouTube",
                    size=12,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=25),
                ft.Row([
                    self.google_loading_ring,
                    self.google_login_button
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                self.status_text,
                self.retry_button,
                ft.Container(height=15),
                ft.Divider(color=ft.Colors.GREY_700, height=1),
                ft.Container(height=5),
                ft.Row([
                    self.guest_loading_ring,
                    self.guest_button
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                self._build_previous_user_section()
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=40,
            border=ft.border.all(1, ft.Colors.GREY_700),
            border_radius=15,
            bgcolor=ft.Colors.with_opacity(0.95, "#1E1E1E"),
            width=500,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.3, "#000000"),
                offset=ft.Offset(0, 4)
            )
        )
        
        # Main layout
        main_content = ft.Column([
            title,
            subtitle,
            ft.Container(height=40),
            login_card,
            ft.Text(
                "Note: Google authentication uses YouTube OAuth for seamless video uploads",
                size=10,
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
        
        return ft.Container(
            content=main_content,
            alignment=ft.alignment.center,
            padding=ft.padding.only(left=40,right=40,bottom=40,top=15),
            expand=True
        )
    
    def _handle_guest_login(self, e):
        """Handle guest login (local only, no database)"""
        if self.is_guest_logging_in:
            return
        
        self._set_guest_loading(True)
        
        try:
            print("Guest login started")
            
            # Create guest role
            guest_role = RoleManager.create_role(RoleType.GUEST)
            print(f"Guest role created: {guest_role.name}")
            
            # Set session info (local session only, no database)
            user_info = {
                'email': 'guest@local',
                'uid': f'guest_{int(__import__("time").time())}',  # Unique guest ID
                'name': 'Guest User',
                'role': 'guest',
                'provider': 'guest',
                'authenticated': False
            }
            print(f"Guest session prepared (local only): {user_info}")
            
            # Call login completion callback
            if self.on_login_complete:
                print("Calling login completion callback")
                self.on_login_complete(user_info, guest_role)
            else:
                print("No login completion callback set!")
            
        except Exception as ex:
            print(f"Guest login exception: {ex}")
            self._show_error(f"Guest login failed: {str(ex)}")
        finally:
            self._set_guest_loading(False)
    
    def _handle_google_login(self, e):
        """Handle Google OAuth login with Firebase integration"""
        if self.is_logging_in:
            return
        
        self._set_loading(True)
        
        # Clear tokens first to force fresh authentication
        from access_control.session import session_manager
        session_manager._clear_oauth_tokens()
        
        try:
            # Use the actual YouTube uploader authentication
            from uploader.auth import get_youtube_service
            
            self._show_status("Check your browser for authentication...")
            self._show_retry_button(True)
            
            # Get YouTube service - this will handle the real OAuth flow
            youtube_service = get_youtube_service()
            
            if not youtube_service or not youtube_service.credentials:
                self._show_error("Google authentication failed")
                self._show_retry_button(True)  # Keep retry button visible on failure
                return
            
            # Get user info from Google's UserInfo API
            self._show_status("Getting user information...")
            self._show_retry_button(False)  # Hide retry button on success
            
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
                    "role": "free",  # Default role for OAuth users
                    "provider": "google",
                    "authenticated": True,
                    "google_id": user_info_response.get('id', ''),
                    "uid": user_info_response.get('id', '')  # Use Google ID as UID
                }
                
            except Exception as userinfo_ex:
                print(f"Could not get user info: {userinfo_ex}")
                # Fallback if userinfo API fails
                user_data = {
                    "email": "authenticated@gmail.com",
                    "name": "Google User",
                    "role": "free",
                    "provider": "google", 
                    "authenticated": True,
                    "uid": "unknown"
                }
            
            # Try to sync with Firebase if available
            self._show_status("Syncing user data...")
            firebase_user_data = None
            
            try:
                from access_control.firebase_service import FirebaseService
                firebase_service = FirebaseService()
                
                # Check if user exists in Firebase, create if not
                firebase_user_data = firebase_service.get_user_by_email(user_data["email"])
                
                if firebase_user_data:
                    # Check if user is disabled
                    if firebase_user_data.get("disabled", False):
                        print(f"Login blocked: User {user_data['email']} is disabled")
                        self._show_error("Your account has been disabled. Please contact support.")
                        self._set_loading(False)
                        return

                    # Update user with Firebase data (may have upgraded role, etc.)
                    user_data.update({
                        "role": firebase_user_data.get("role", "free"),
                        "usage_count": firebase_user_data.get("usage_count", 0),
                        "daily_usage": firebase_user_data.get("daily_usage", 0),
                        "premium_until": firebase_user_data.get("premium_until"),
                        "created_at": firebase_user_data.get("created_at"),
                        "last_login": firebase_user_data.get("last_login")
                    })
                    print(f"Loaded existing Firebase user with role: {user_data['role']}")
                else:
                    # Create new user in Firebase
                    firebase_user_data = firebase_service.create_user(user_data)
                    print(f"Created new Firebase user with role: {user_data['role']}")
                    
                # Update last login using email (document ID)
                firebase_service.update_user_last_login(user_data["email"])
                
            except Exception as firebase_ex:
                print(f"Firebase sync failed (continuing without): {firebase_ex}")
                # Continue without Firebase if it's not available
            
            # Create role object based on final role (may have been updated from Firebase)
            role = RoleManager.create_role_by_name(user_data["role"])
            
            # Authenticate with session manager - this saves the session
            session_manager.login(user_data, role)
            
            self._show_status("Authentication successful!")
            self._show_retry_button(False)  # Hide retry button on success
            
            # Call login completion callback
            if self.on_login_complete:
                self.on_login_complete(user_data, role)
            else:
                self._show_error("No login completion callback set!")
                self._show_retry_button(True)
                
        except Exception as ex:
            print(f"OAuth error: {ex}")
            self._show_error(f"Authentication failed: {str(ex)}")
            self._show_retry_button(True)  # Keep retry button visible on error
            
        finally:
            self._set_loading(False)
    
    def _set_loading(self, loading: bool):
        """Show/hide loading indicator for Google login"""
        self.is_logging_in = loading
        self.google_loading_ring.visible = loading
        self.google_login_button.disabled = loading
        
        if loading:
            self.google_login_button.text = "Authenticating..."
            self._hide_error()
        else:
            self.google_login_button.text = "Sign in with Google"
        
        self.page.update()
    
    def _set_guest_loading(self, loading: bool):
        """Show/hide loading indicator for guest login"""
        self.is_guest_logging_in = loading
        self.guest_loading_ring.visible = loading
        self.guest_button.disabled = loading
        
        if loading:
            self.guest_button.text = "Loading..."
        else:
            self.guest_button.text = "Continue as Guest"
        
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
    
    def _show_retry_button(self, show: bool):
        """Show/hide retry button for browser authentication issues"""
        if self.retry_button:
            self.retry_button.visible = show
            self.page.update()
    
    def _handle_retry_auth(self, e):
        """Handle retry authentication if browser didn't open"""
        # Reset loading state first so new auth attempt can proceed
        self.is_logging_in = False
        self.google_loading_ring.visible = False
        self.google_login_button.disabled = False
        self.google_login_button.text = "Sign in with Google"
        self.page.update()
        
        # Now trigger new authentication attempt
        self._handle_google_login(e)
    
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
            role = RoleManager.create_role_by_name(last_user.get('role', 'free'))
            
            # Call login completion callback
            if self.on_login_complete:
                self.on_login_complete(last_user, role)
            else:
                self._show_error("No login completion callback set!")
                
        except Exception as ex:
            print(f"Previous user login error: {ex}")
            self._show_error(f"Failed to login as previous user: {str(ex)}")
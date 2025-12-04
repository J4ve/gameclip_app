"""
Flet login screen for Firebase/Google authentication
"""

import flet as ft
import pyrebase

# Firebase client config (web app credentials, not service account)
# Get these from Firebase Console → Project Settings → Your apps → Web app
FIREBASE_CONFIG = {
    "apiKey": "YOUR_API_KEY",  # Replace with your Firebase web API key
    "authDomain": "YOUR_PROJECT_ID.firebaseapp.com",
    "databaseURL": "https://YOUR_PROJECT_ID.firebaseio.com",
    "projectId": "YOUR_PROJECT_ID",
    "storageBucket": "YOUR_PROJECT_ID.appspot.com",
    "messagingSenderId": "YOUR_SENDER_ID",
    "appId": "YOUR_APP_ID"
}

class LoginScreen:
    """
    Login screen for Firebase/Google authentication.
    After successful login, passes ID token to parent app.
    """
    
    def __init__(self, page: ft.Page, on_login_success=None):
        self.page = page
        self.on_login_success = on_login_success
        self.firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
        self.auth = self.firebase.auth()
        
        # UI elements
        self.email_field = None
        self.password_field = None
        self.error_text = None
    
    def build(self):
        """Build login screen UI."""
        self.email_field = ft.TextField(
            label="Email",
            width=300,
            autofocus=True
        )
        
        self.password_field = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            width=300
        )
        
        self.error_text = ft.Text("", color=ft.colors.RED, size=12)
        
        login_button = ft.ElevatedButton(
            "Sign In",
            on_click=self._handle_login,
            width=300
        )
        
        google_button = ft.ElevatedButton(
            "Sign in with Google",
            icon=ft.icons.LOGIN,
            on_click=self._handle_google_login,
            width=300
        )
        
        signup_button = ft.TextButton(
            "Create account",
            on_click=self._handle_signup
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Video Merger App", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Sign in to upload videos", size=14, color=ft.colors.GREY),
                ft.Container(height=20),
                self.email_field,
                self.password_field,
                self.error_text,
                login_button,
                ft.Container(height=10),
                ft.Divider(),
                google_button,
                signup_button,
                ft.Container(height=20),
                ft.Text("Guest mode: Limited features with ads", size=12, color=ft.colors.GREY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
    
    def _handle_login(self, e):
        """Handle email/password login."""
        email = self.email_field.value
        password = self.password_field.value
        
        if not email or not password:
            self.error_text.value = "Email and password required"
            self.page.update()
            return
        
        try:
            # Sign in with email/password
            user = self.auth.sign_in_with_email_and_password(email, password)
            id_token = user['idToken']
            
            # Call success callback with token
            if self.on_login_success:
                self.on_login_success(id_token)
        except Exception as ex:
            self.error_text.value = f"Login failed: {str(ex)}"
            self.page.update()
    
    def _handle_google_login(self, e):
        """Handle Google OAuth login."""
        # Note: Google OAuth in desktop apps requires opening browser
        # This is a placeholder - full implementation needs OAuth flow
        self.error_text.value = "Google login: Open browser to authorize (not implemented in skeleton)"
        self.page.update()
        
        # TODO: Implement Google OAuth flow:
        # 1. Generate auth URL with Firebase
        # 2. Open browser to auth URL
        # 3. Handle redirect with code
        # 4. Exchange code for ID token
        # 5. Call on_login_success(id_token)
    
    def _handle_signup(self, e):
        """Handle signup (create new account)."""
        email = self.email_field.value
        password = self.password_field.value
        
        if not email or not password:
            self.error_text.value = "Email and password required"
            self.page.update()
            return
        
        try:
            # Create new user
            user = self.auth.create_user_with_email_and_password(email, password)
            id_token = user['idToken']
            
            # Call success callback with token
            if self.on_login_success:
                self.on_login_success(id_token)
        except Exception as ex:
            self.error_text.value = f"Signup failed: {str(ex)}"
            self.page.update()

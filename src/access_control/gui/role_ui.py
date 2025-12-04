"""
Role-based UI components for Flet
Conditionally shows/hides features based on user role
"""

import flet as ft
from access_control.auth.user_session import user_session

class RoleBasedContainer(ft.Container):
    """
    Container that shows/hides content based on user role.
    
    Usage:
        RoleBasedContainer(
            content=ft.Text("Premium feature!"),
            required_roles=['premium', 'admin']
        )
    """
    
    def __init__(self, content, required_roles=None, **kwargs):
        super().__init__(content=content, **kwargs)
        self.required_roles = required_roles or []
        self.update_visibility()
    
    def update_visibility(self):
        """Update visibility based on current user role."""
        if not self.required_roles:
            self.visible = True
        else:
            self.visible = user_session.has_role(*self.required_roles)


class AdBanner(ft.Container):
    """
    Ad banner that shows for guest/normal users, hidden for premium.
    
    Usage:
        AdBanner()
    """
    
    def __init__(self, **kwargs):
        content = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.ADS_CLICK, color=ft.colors.YELLOW),
                ft.Text("Advertisement - Upgrade to Premium to remove ads", size=12),
            ]),
            bgcolor=ft.colors.BLACK26,
            padding=10,
            border_radius=5
        )
        
        super().__init__(content=content, **kwargs)
        self.update_visibility()
    
    def update_visibility(self):
        """Show ads for guest/normal, hide for premium/dev/admin."""
        self.visible = not user_session.is_premium()


class AdminPanel(ft.Container):
    """
    Admin-only panel for user management.
    
    Usage:
        AdminPanel(on_role_change=callback)
    """
    
    def __init__(self, on_role_change=None, **kwargs):
        from access_control.auth.firebase_auth import firebase_auth
        
        self.on_role_change = on_role_change
        self.firebase_auth = firebase_auth
        self.users_list = ft.Column(scroll=ft.ScrollMode.AUTO)
        
        content = ft.Container(
            content=ft.Column([
                ft.Text("Admin Panel", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.ElevatedButton("Refresh Users", on_click=self._load_users),
                self.users_list
            ]),
            padding=20,
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=10
        )
        
        super().__init__(content=content, **kwargs)
        self.update_visibility()
        self._load_users()
    
    def update_visibility(self):
        """Show only for admins."""
        self.visible = user_session.is_admin()
    
    def _load_users(self, e=None):
        """Load and display users."""
        users = self.firebase_auth.list_users()
        self.users_list.controls.clear()
        
        for user in users:
            self.users_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.PERSON),
                    title=ft.Text(user['email'] or user['uid']),
                    subtitle=ft.Text(f"Role: {user['role']}"),
                    trailing=ft.Dropdown(
                        width=150,
                        value=user['role'],
                        options=[
                            ft.dropdown.Option("guest"),
                            ft.dropdown.Option("normal"),
                            ft.dropdown.Option("premium"),
                            ft.dropdown.Option("dev"),
                            ft.dropdown.Option("admin"),
                        ],
                        on_change=lambda e, uid=user['uid']: self._change_role(uid, e.data)
                    )
                )
            )
    
    def _change_role(self, uid: str, new_role: str):
        """Change user role."""
        success = self.firebase_auth.set_user_role(uid, new_role)
        if success and self.on_role_change:
            self.on_role_change(uid, new_role)


class DevLogsPanel(ft.Container):
    """
    Developer logs panel (dev/admin only).
    
    Usage:
        DevLogsPanel()
    """
    
    def __init__(self, **kwargs):
        self.logs = ft.Column(scroll=ft.ScrollMode.AUTO, height=400)
        
        content = ft.Container(
            content=ft.Column([
                ft.Text("Developer Logs", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.logs
            ]),
            padding=15,
            bgcolor=ft.colors.BLACK,
            border_radius=8
        )
        
        super().__init__(content=content, **kwargs)
        self.update_visibility()
    
    def update_visibility(self):
        """Show only for dev/admin."""
        self.visible = user_session.is_dev()
    
    def add_log(self, message: str, level: str = "INFO"):
        """Add a log message."""
        color = {
            "INFO": ft.colors.WHITE,
            "WARN": ft.colors.YELLOW,
            "ERROR": ft.colors.RED,
            "DEBUG": ft.colors.CYAN
        }.get(level, ft.colors.WHITE)
        
        self.logs.controls.append(
            ft.Text(f"[{level}] {message}", color=color, size=12)
        )
        
        # Keep only last 100 logs
        if len(self.logs.controls) > 100:
            self.logs.controls.pop(0)

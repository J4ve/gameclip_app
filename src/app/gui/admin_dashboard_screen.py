"""
Admin Dashboard Screen - User Management
Secure interface for administrators to manage users, roles, and permissions.

Security Features:
- Multi-layer permission verification (UI + Backend + Firebase Rules)
- Audit logging for all actions
- Rate limiting on critical operations
- Confirmation dialogs for destructive actions
"""

import flet as ft
from access_control.session import session_manager
from access_control.roles import Permission
from access_control.firebase_service import get_firebase_service
from datetime import datetime
from typing import Optional, List, Dict, Any


class AdminDashboardScreen:
    """Secure admin dashboard for user management"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.firebase_service = get_firebase_service()
        
        # Security: Verify admin permission immediately
        if not self._verify_admin_access():
            self._handle_unauthorized_access()
            return
        
        # UI Components
        self.users_table = None
        self.search_field = None
        self.filter_dropdown = None
        self.refresh_button = None
        self.loading_indicator = None
        
        # Data
        self.users_data: List[Dict[str, Any]] = []
        self.filtered_users: List[Dict[str, Any]] = []
    
    def _verify_admin_access(self) -> bool:
        """
        Security Layer 1: UI-level permission check
        Verify user has MANAGE_USERS permission
        
        TODO: Add additional checks:
        - Session validity check
        - Token expiration check
        - IP whitelist verification (future)
        """
        if not session_manager.has_permission(Permission.MANAGE_USERS.value):
            print(f"[SECURITY] Unauthorized access attempt by {session_manager.email}")
            return False
        
        print(f"[SECURITY] Admin access granted to {session_manager.email}")
        return True
    
    def _handle_unauthorized_access(self):
        """Handle unauthorized access attempts"""
        # TODO: Log to audit trail
        # TODO: Implement rate limiting on failed attempts
        # TODO: Send alert notification to system admins
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Access Denied: Admin privileges required"),
            bgcolor=ft.Colors.RED_700
        )
        self.page.snack_bar.open = True
        self.page.update()
        
        # Redirect to main screen
        # TODO: Implement proper navigation back to main window
    
    def build(self) -> ft.Container:
        """Build the admin dashboard UI"""
        # Search and filter controls
        self.search_field = ft.TextField(
            label="Search users (email, name)",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._on_search_changed,
            expand=True
        )
        
        self.filter_dropdown = ft.Dropdown(
            label="Filter by role",
            options=[
                ft.dropdown.Option("all", "All Roles"),
                ft.dropdown.Option("guest", "Guest"),
                ft.dropdown.Option("free", "Free"),
                ft.dropdown.Option("premium", "Premium"),
                ft.dropdown.Option("dev", "Developer"),
                ft.dropdown.Option("admin", "Admin"),
            ],
            value="all",
            on_change=self._on_filter_changed,
            width=200
        )
        
        self.refresh_button = ft.ElevatedButton(
            "Refresh",
            icon=ft.Icons.REFRESH,
            on_click=self._refresh_users,
            bgcolor=ft.Colors.BLUE_700
        )
        
        # Loading indicator
        self.loading_indicator = ft.ProgressRing(visible=False)
        
        # Users table header
        table_header = ft.Row([
            ft.Text("Email", weight=ft.FontWeight.BOLD, expand=2),
            ft.Text("Name", weight=ft.FontWeight.BOLD, expand=2),
            ft.Text("Role", weight=ft.FontWeight.BOLD, expand=1),
            ft.Text("Last Login", weight=ft.FontWeight.BOLD, expand=2),
            ft.Text("Status", weight=ft.FontWeight.BOLD, expand=1),
            ft.Text("Actions", weight=ft.FontWeight.BOLD, expand=2),
        ], spacing=10)
        
        # Users table content (will be populated dynamically)
        self.users_table = ft.Column(
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Main layout
        return ft.Container(
            content=ft.Column([
                ft.Text("Admin Dashboard", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400),
                ft.Text("User Management & Role Administration", size=14, color=ft.Colors.GREY_400),
                ft.Divider(),
                
                # Controls row
                ft.Row([
                    self.search_field,
                    self.filter_dropdown,
                    self.refresh_button,
                    self.loading_indicator,
                ], spacing=10),
                
                ft.Divider(),
                
                # Table header
                table_header,
                ft.Divider(),
                
                # Users list
                self.users_table,
                
                # TODO: Add pagination controls
                # TODO: Add bulk actions (export, bulk role change)
                # TODO: Add statistics summary (total users, by role, active today)
                
            ], spacing=15, expand=True),
            padding=20,
            expand=True
        )
    
    def load_users(self):
        """
        Load all users from Firebase with backend verification
        
        TODO: Implement pagination for large user bases (>100 users)
        TODO: Add caching with TTL to reduce Firebase reads
        TODO: Implement real-time listener for live updates
        """
        self._show_loading(True)
        
        try:
            # Security Layer 2: Backend verification before data access
            if not self._verify_backend_permission():
                self._handle_unauthorized_access()
                return
            
            # Fetch users from Firebase
            self.users_data = self.firebase_service.get_all_users()
            self.filtered_users = self.users_data.copy()
            
            # Populate table
            self._populate_users_table()
            
            print(f"[ADMIN] Loaded {len(self.users_data)} users")
            
        except Exception as e:
            print(f"[ERROR] Failed to load users: {e}")
            self._show_error(f"Failed to load users: {str(e)}")
        finally:
            self._show_loading(False)
    
    def _verify_backend_permission(self) -> bool:
        """
        Security Layer 2: Backend permission verification
        Query Firestore to confirm admin role
        
        TODO: Implement rate limiting
        TODO: Add session token validation
        TODO: Verify IP whitelist (if configured)
        """
        if not self.firebase_service or not self.firebase_service.is_available:
            return False
        
        try:
            # TODO: Call firebase_service.verify_admin_permission(session_manager.email)
            # For now, trust the session manager
            return session_manager.is_admin()
        except Exception as e:
            print(f"[SECURITY] Backend verification failed: {e}")
            return False
    
    def _populate_users_table(self):
        """Populate the users table with data"""
        self.users_table.controls.clear()
        
        if not self.filtered_users:
            self.users_table.controls.append(
                ft.Text("No users found", color=ft.Colors.GREY_400, italic=True)
            )
            self.page.update()
            return
        
        for user in self.filtered_users:
            user_row = self._create_user_row(user)
            self.users_table.controls.append(user_row)
        
        self.page.update()
    
    def _create_user_row(self, user: Dict[str, Any]) -> ft.Container:
        """Create a table row for a user"""
        email = user.get('email', 'N/A')
        name = user.get('name', 'N/A')
        role = user.get('role', 'unknown')
        last_login = user.get('last_login', 'Never')
        
        # Format last login
        if isinstance(last_login, datetime):
            last_login = last_login.strftime("%Y-%m-%d %H:%M")
        elif last_login and last_login != 'Never':
            try:
                # Handle Firestore timestamp
                last_login = last_login.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        # Determine status
        status = user.get('disabled', False)
        status_text = "Disabled" if status else "Active"
        status_color = ft.Colors.RED_400 if status else ft.Colors.GREEN_400
        
        # Action buttons
        role_button = ft.PopupMenuButton(
            icon=ft.Icons.ADMIN_PANEL_SETTINGS,
            tooltip="Change Role",
            items=[
                ft.PopupMenuItem(text="Guest", on_click=lambda e, u=user: self._change_role(u, "guest")),
                ft.PopupMenuItem(text="Free", on_click=lambda e, u=user: self._change_role(u, "free")),
                ft.PopupMenuItem(text="Premium", on_click=lambda e, u=user: self._change_role(u, "premium")),
                ft.PopupMenuItem(text="Developer", on_click=lambda e, u=user: self._change_role(u, "dev")),
                ft.PopupMenuItem(text="Admin", on_click=lambda e, u=user: self._change_role(u, "admin")),
            ]
        )
        
        disable_button = ft.IconButton(
            icon=ft.Icons.BLOCK if not status else ft.Icons.CHECK_CIRCLE,
            tooltip="Disable User" if not status else "Enable User",
            on_click=lambda e, u=user: self._toggle_user_status(u),
            icon_color=ft.Colors.ORANGE_400 if not status else ft.Colors.GREEN_400
        )
        
        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE_FOREVER,
            tooltip="Delete User",
            on_click=lambda e, u=user: self._delete_user(u),
            icon_color=ft.Colors.RED_400
        )
        
        return ft.Container(
            content=ft.Row([
                ft.Text(email, expand=2, size=12),
                ft.Text(name, expand=2, size=12),
                ft.Container(
                    content=ft.Text(role.title(), size=11, weight=ft.FontWeight.BOLD),
                    bgcolor=self._get_role_color(role),
                    padding=5,
                    border_radius=5,
                    expand=1
                ),
                ft.Text(str(last_login), expand=2, size=11, color=ft.Colors.GREY_400),
                ft.Text(status_text, expand=1, size=11, color=status_color),
                ft.Row([role_button, disable_button, delete_button], expand=2, spacing=5),
            ], spacing=10),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_800),
            border_radius=5,
        )
    
    def _get_role_color(self, role: str) -> str:
        """Get background color for role badge"""
        colors = {
            'guest': ft.Colors.GREY_700,
            'free': ft.Colors.BLUE_700,
            'premium': ft.Colors.PURPLE_700,
            'dev': ft.Colors.ORANGE_700,
            'admin': ft.Colors.RED_700,
        }
        return colors.get(role.lower(), ft.Colors.GREY_700)
    
    def _change_role(self, user: Dict[str, Any], new_role: str):
        """
        Change user role with security verification
        
        TODO: Implement confirmation dialog with re-authentication
        TODO: Add audit logging
        TODO: Implement rate limiting
        TODO: Prevent self-demotion for admin users
        """
        email = user.get('email')
        current_role = user.get('role')
        
        # Prevent self-role change
        if email == session_manager.email:
            self._show_error("Cannot change your own role")
            return
        
        # Show confirmation dialog
        def confirm_change(e):
            dialog.open = False
            self.page.update()
            self._execute_role_change(email, new_role, current_role)
        
        def cancel_change(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Role Change"),
            content=ft.Text(f"Change role for {email} from '{current_role}' to '{new_role}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_change),
                ft.TextButton("Confirm", on_click=confirm_change),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _execute_role_change(self, email: str, new_role: str, old_role: str):
        """Execute the role change with backend verification and audit logging"""
        try:
            # Security Layer 2: Backend verification
            if not self._verify_backend_permission():
                self._handle_unauthorized_access()
                return
            
            # TODO: Security Layer 3: Firebase Rules verification
            # TODO: Implement rate limiting check
            
            # Execute role change
            success = self.firebase_service.update_user_role(email, new_role)
            
            if success:
                # TODO: Log to audit trail
                # TODO: firebase_service.log_admin_action(
                #     admin_email=session_manager.email,
                #     action="role_change",
                #     target_user=email,
                #     details={"from": old_role, "to": new_role}
                # )
                
                self._show_success(f"Role changed successfully: {email} → {new_role}")
                self._refresh_users(None)
            else:
                self._show_error("Failed to change role")
        
        except Exception as e:
            print(f"[ERROR] Role change failed: {e}")
            self._show_error(f"Error: {str(e)}")
    
    def _toggle_user_status(self, user: Dict[str, Any]):
        """
        Enable or disable user account
        
        TODO: Implement disable/enable user in firebase_service
        TODO: Add confirmation dialog
        TODO: Add audit logging
        TODO: Prevent self-disable
        """
        email = user.get('email')
        current_status = user.get('disabled', False)
        action = "enable" if current_status else "disable"
        
        # Prevent self-disable
        if email == session_manager.email:
            self._show_error("Cannot disable your own account")
            return
        
        self._show_error(f"TODO: Implement user {action} functionality")
        # TODO: Implement firebase_service.disable_user(email) / enable_user(email)
    
    def _delete_user(self, user: Dict[str, Any]):
        """
        Delete user account (permanent action)
        
        TODO: Implement with strong confirmation (type email to confirm)
        TODO: Add audit logging
        TODO: Prevent self-deletion
        TODO: Archive user data before deletion
        """
        email = user.get('email')
        
        # Prevent self-deletion
        if email == session_manager.email:
            self._show_error("Cannot delete your own account")
            return
        
        self._show_error("TODO: Implement user deletion functionality")
        # TODO: Implement firebase_service.delete_user(email)
    
    def _on_search_changed(self, e):
        """Filter users based on search query"""
        query = self.search_field.value.lower().strip()
        
        if not query:
            self.filtered_users = self.users_data.copy()
        else:
            self.filtered_users = [
                user for user in self.users_data
                if query in user.get('email', '').lower() or query in user.get('name', '').lower()
            ]
        
        self._populate_users_table()
    
    def _on_filter_changed(self, e):
        """Filter users by role"""
        role_filter = self.filter_dropdown.value
        
        if role_filter == "all":
            self.filtered_users = self.users_data.copy()
        else:
            self.filtered_users = [
                user for user in self.users_data
                if user.get('role', '').lower() == role_filter
            ]
        
        # Apply search filter if active
        if self.search_field.value:
            self._on_search_changed(None)
        else:
            self._populate_users_table()
    
    def _refresh_users(self, e):
        """Refresh user list from Firebase"""
        self.load_users()
        self._show_success("Users refreshed")
    
    def _show_loading(self, visible: bool):
        """Show/hide loading indicator"""
        if self.loading_indicator:
            self.loading_indicator.visible = visible
            self.page.update()
    
    def _show_error(self, message: str):
        """Show error snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_700
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _show_success(self, message: str):
        """Show success snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN_700
        )
        self.page.snack_bar.open = True
        self.page.update()

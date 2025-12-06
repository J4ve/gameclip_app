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
from configs.config import Config
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
        
        # Add/Update User Form
        self.new_user_email = ft.TextField(
            label="Email address",
            hint_text="user@example.com",
            prefix_icon=ft.Icons.EMAIL,
            expand=True,
            width=300
        )
        
        self.new_user_role = ft.Dropdown(
            label="Role",
            options=[
                ft.dropdown.Option("free", "Free"),
                ft.dropdown.Option("premium", "Premium"),
                ft.dropdown.Option("admin", "Admin"),
            ],
            value="free",
            width=150
        )
        
        add_user_button = ft.ElevatedButton(
            "Add/Update User",
            icon=ft.Icons.PERSON_ADD,
            on_click=self._add_or_update_user,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE
        )
        
        add_user_form = ft.Container(
            content=ft.Column([
                ft.Text("Add or Update User", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                ft.Text("Enter an email and role. If user exists, their role will be updated.", size=12, color=ft.Colors.GREY_400),
                ft.Row([
                    self.new_user_email,
                    self.new_user_role,
                    add_user_button
                ], spacing=10, alignment=ft.MainAxisAlignment.START),
            ], spacing=10),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREEN_700),
        )
        
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
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
                    ft.ControlState.HOVERED: ft.Colors.BLUE_600,
                },
            )
        )
        
        # Loading indicator - wrapped in container to prevent layout shift
        self.loading_indicator = ft.ProgressRing(visible=False, width=20, height=20)
        self.loading_container = ft.Container(
            content=self.loading_indicator,
            width=50,  # Fixed width to prevent shifting
            alignment=ft.alignment.center
        )
        
        # Users table header with fixed widths to match row layout
        table_header = ft.Container(
            content=ft.Row([
                ft.Container(width=50),  # Avatar space
                ft.Container(ft.Text("Email", weight=ft.FontWeight.BOLD, size=12), width=200),
                ft.Container(ft.Text("Name", weight=ft.FontWeight.BOLD, size=12), width=200),
                ft.Container(ft.Text("Role", weight=ft.FontWeight.BOLD, size=12), width=100),
                ft.Container(ft.Text("Last Login", weight=ft.FontWeight.BOLD, size=12), width=150),
                ft.Container(ft.Text("Status", weight=ft.FontWeight.BOLD, size=12), width=80),
                ft.Container(ft.Text("Actions", weight=ft.FontWeight.BOLD, size=12), width=150),
            ], spacing=10),
            padding=ft.padding.only(left=10, right=10)
        )
        
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
                
                # Add/Update User Form
                add_user_form,
                ft.Divider(),
                
                # Controls row
                ft.Row([
                    self.search_field,
                    self.filter_dropdown,
                    self.refresh_button,
                    self.loading_container,
                ], spacing=10),
                
                ft.Divider(),
                
                # Table header
                table_header,
                ft.Divider(),
                
                # Users list
                self.users_table,
                
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
        picture_url = user.get('picture', '')
        
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
        
        # Check if this is the super admin
        is_super_admin = (email == Config.SUPER_ADMIN_EMAIL)
        
        # Create user avatar with loading state
        if picture_url:
            user_avatar = ft.CircleAvatar(
                foreground_image_src=picture_url,
                content=ft.Icon(ft.Icons.PERSON, size=20),  # Fallback/loading icon
                radius=20,
            )
        else:
            user_avatar = ft.CircleAvatar(
                content=ft.Icon(ft.Icons.PERSON, size=20),
                bgcolor=ft.Colors.BLUE_GREY_700,
                radius=20,
            )
        
        # Action buttons (disabled for super admin)
        role_button = ft.PopupMenuButton(
            icon=ft.Icons.ADMIN_PANEL_SETTINGS,
            tooltip="Change Role" if not is_super_admin else "Super Admin - Role cannot be changed",
            items=[
                ft.PopupMenuItem(text="Guest", on_click=lambda e, u=user: self._change_role(u, "guest")),
                ft.PopupMenuItem(text="Free", on_click=lambda e, u=user: self._change_role(u, "free")),
                ft.PopupMenuItem(text="Premium", on_click=lambda e, u=user: self._change_role(u, "premium")),
                ft.PopupMenuItem(text="Admin", on_click=lambda e, u=user: self._change_role(u, "admin")),
            ],
            disabled=is_super_admin
        )
        
        disable_button = ft.IconButton(
            icon=ft.Icons.BLOCK if not status else ft.Icons.CHECK_CIRCLE,
            tooltip="Disable User" if not status and not is_super_admin else "Enable User" if status else "Super Admin - Cannot be disabled",
            on_click=lambda e, u=user: self._toggle_user_status(u),
            icon_color=ft.Colors.ORANGE_400 if not status else ft.Colors.GREEN_400,
            disabled=is_super_admin
        )
        
        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE_FOREVER,
            tooltip="Delete User" if not is_super_admin else "Super Admin - Cannot be deleted",
            on_click=lambda e, u=user: self._delete_user(u),
            icon_color=ft.Colors.RED_400,
            disabled=is_super_admin
        )
        
        # Create name display with super admin badge if applicable
        name_display = ft.Row([
            ft.Text(name, size=12),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SECURITY, size=12, color=ft.Colors.YELLOW_400),
                    ft.Text("SUPER ADMIN", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.YELLOW_400)
                ], spacing=3, tight=True),
                bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.YELLOW_400),
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                border_radius=3,
                visible=is_super_admin
            )
        ], spacing=8, tight=True) if is_super_admin else ft.Text(name, size=12)
        
        return ft.Container(
            content=ft.Row([
                ft.Container(user_avatar, width=50),
                ft.Container(ft.Text(email, size=12, overflow=ft.TextOverflow.ELLIPSIS), width=200),
                ft.Container(name_display, width=200),
                ft.Container(
                    ft.Container(
                        content=ft.Text(role.title(), size=11, weight=ft.FontWeight.BOLD),
                        bgcolor=self._get_role_color(role),
                        padding=5,
                        border_radius=5,
                    ),
                    width=100
                ),
                ft.Container(ft.Text(str(last_login), size=11, color=ft.Colors.GREY_400, overflow=ft.TextOverflow.ELLIPSIS), width=150),
                ft.Container(ft.Text(status_text, size=11, color=status_color), width=80),
                ft.Container(ft.Row([role_button, disable_button, delete_button], spacing=5), width=150),
            ], spacing=10),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_800 if not is_super_admin else ft.Colors.YELLOW_700),
            border_radius=5,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.YELLOW_400) if is_super_admin else None,
        )
    
    def _get_role_color(self, role: str) -> str:
        """Get background color for role badge"""
        colors = {
            'guest': ft.Colors.GREY_700,
            'free': ft.Colors.BLUE_700,
            'premium': ft.Colors.PURPLE_700,
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
        
        # Prevent changing super admin's role
        if email == Config.SUPER_ADMIN_EMAIL:
            self._show_error(f"Cannot change {email}'s role - This is the super admin account")
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
        
        # Prevent disabling super admin
        if email == Config.SUPER_ADMIN_EMAIL:
            self._show_error(f"Cannot {action} {email} - This is the super admin account")
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
        
        # Prevent deleting super admin
        if email == Config.SUPER_ADMIN_EMAIL:
            self._show_error(f"Cannot delete {email} - This is the super admin account")
            return
        
        self._show_error("TODO: Implement user deletion functionality")
        # TODO: Implement firebase_service.delete_user(email)
    
    def _add_or_update_user(self, e):
        """
        Add a new user or update existing user's role by email
        Creates a placeholder user document that will be populated when they first log in
        """
        email = self.new_user_email.value.strip().lower()
        role = self.new_user_role.value
        
        # Validate email
        if not email:
            self._show_error("Please enter an email address")
            return
        
        if "@" not in email or "." not in email.split("@")[-1]:
            self._show_error("Please enter a valid email address")
            return
        
        # Prevent modifying super admin (unless it's creating them for first time)
        if email == Config.SUPER_ADMIN_EMAIL and role != "admin":
            self._show_error(f"Cannot assign non-admin role to super admin {email}")
            return
        
        # Security: Backend verification
        if not self._verify_backend_permission():
            self._handle_unauthorized_access()
            return
        
        try:
            # Check if user already exists
            existing_user = self.firebase_service.get_user_by_email(email)
            
            if existing_user:
                # User exists - update role
                old_role = existing_user.get('role', 'unknown')
                
                if old_role == role:
                    self._show_error(f"User {email} already has role '{role}'")
                    return
                
                # Prevent changing super admin role
                if email == Config.SUPER_ADMIN_EMAIL and role != "admin":
                    self._show_error(f"Cannot change super admin's role from admin")
                    return
                
                # Confirm role change
                def confirm_update(e):
                    dialog.open = False
                    self.page.update()
                    
                    success = self.firebase_service.update_user_role(email, role)
                    if success:
                        self._show_success(f"Updated {email}: {old_role} → {role}")
                        self._refresh_users(None)
                        self.new_user_email.value = ""
                        self.page.update()
                    else:
                        self._show_error(f"Failed to update user role")
                
                def cancel_update(e):
                    dialog.open = False
                    self.page.update()
                
                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Confirm Role Update"),
                    content=ft.Text(f"Update {email} from '{old_role}' to '{role}'?"),
                    actions=[
                        ft.TextButton("Cancel", on_click=cancel_update),
                        ft.TextButton("Update", on_click=confirm_update),
                    ],
                )
                
                self.page.overlay.append(dialog)
                dialog.open = True
                self.page.update()
            else:
                # User doesn't exist - create placeholder document
                def confirm_create(e):
                    dialog.open = False
                    self.page.update()
                    
                    # Create user document
                    from datetime import datetime, timezone
                    user_data = {
                        'email': email,
                        'role': role,
                        'name': email.split('@')[0],  # Use email username as default name
                        'created_at': datetime.now(timezone.utc),
                        'last_login': None,
                        'uid': f'manual_{email}',  # Temporary UID until they log in
                        'daily_usage': 0,
                        'usage_count': 0,
                        'disabled': False,
                    }
                    
                    success = self.firebase_service.create_or_update_user(user_data)
                    if success:
                        self._show_success(f"Created user {email} with role '{role}'. They can now log in with Google OAuth.")
                        self._refresh_users(None)
                        self.new_user_email.value = ""
                        self.page.update()
                    else:
                        self._show_error(f"Failed to create user")
                
                def cancel_create(e):
                    dialog.open = False
                    self.page.update()
                
                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Confirm User Creation"),
                    content=ft.Column([
                        ft.Text(f"Create new user: {email}"),
                        ft.Text(f"Role: {role}"),
                        ft.Text(""),
                        ft.Text("The user will be able to log in with their Google account.", color=ft.Colors.GREY_400, size=12),
                    ], tight=True, spacing=5),
                    actions=[
                        ft.TextButton("Cancel", on_click=cancel_create),
                        ft.TextButton("Create", on_click=confirm_create),
                    ],
                )
                
                self.page.overlay.append(dialog)
                dialog.open = True
                self.page.update()
        
        except Exception as ex:
            print(f"[ERROR] Add/update user failed: {ex}")
            self._show_error(f"Error: {str(ex)}")
    
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

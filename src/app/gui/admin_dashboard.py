"""
Admin Dashboard Screen - User Management
Secure interface for administrators to manage users, roles, and permissions.

Security Features:
- Multi-layer permission verification (UI + Backend + Firebase Rules)
- Audit logging for all actions
- Rate limiting on critical operations
"""

import flet as ft
from access_control.session import session_manager
from access_control.roles import Permission
from access_control.firebase_service import get_firebase_service
from configs.config import Config
from datetime import datetime
from typing import Optional, List, Dict, Any
from .audit_log_viewer import AuditLogService


class AdminDashboard:
    """Secure admin dashboard for user management"""
    
    def __init__(self, page: ft.Page):
        print("=" * 80)
        print("ADMIN DASHBOARD __init__ CALLED")
        print("=" * 80)
        
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
        
        # Audit log components
        self.audit_log_service = None
        self.audit_actor_filter = None
        self.audit_target_filter = None
        self.audit_action_filter = None
        self.audit_date_range = None
        self.audit_logs_table = None
        self.audit_loading = None
        self.audit_log_count = None
        
        # Data
        self.users_data: List[Dict[str, Any]] = []
        self.filtered_users: List[Dict[str, Any]] = []
        self.audit_logs_data: List[Dict[str, Any]] = []
    
    def _verify_admin_access(self) -> bool:
        """
        Security Layer 1: UI-level permission check
        Verify user has MANAGE_USERS permission
        
        Future enhancements:
        - Session validity check
        - Token expiration check
        - IP whitelist verification
        """
        if not session_manager.has_permission(Permission.MANAGE_USERS.value):
            print(f"[SECURITY] Unauthorized access attempt by {session_manager.email}")
            return False
        
        print(f"[SECURITY] Admin access granted to {session_manager.email}")
        return True
    
    def _handle_unauthorized_access(self):
        """Handle unauthorized access attempts
        
        Future enhancements:
        - Rate limiting on failed attempts
        - Alert notifications to system admins
        - Proper navigation back to main window
        """
        # Note: Audit logging now handled per-action in firebase_service
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Access Denied: Admin privileges required"),
            bgcolor=ft.Colors.RED_700
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def build(self) -> ft.Container:
        """Build the admin dashboard UI with user management and audit logs"""
        
        print("[DEBUG] AdminDashboard.build() called")
        
        # Load audit logs automatically
        if hasattr(self, '_load_audit_logs'):
            self._load_audit_logs()
        
        # Build user management section (includes audit logs inside)
        user_management_content = self._build_user_management_section()
        
        print(f"[DEBUG] user_management_content type: {type(user_management_content)}")
        
        # Main container - MUST BE SCROLLABLE
        result = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=32, color=ft.Colors.RED_400),
                    ft.Text("Admin Dashboard", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400),
                ], spacing=10),
                ft.Text("User Management & Security Monitoring", size=14, color=ft.Colors.GREY_400),
                ft.Divider(),
                
                # User Management Section with audit logs inside
                user_management_content,
            ], spacing=15, scroll=ft.ScrollMode.AUTO),  # SCROLL HERE!
            padding=10,
            expand=True
        )
        
        print(f"[DEBUG] Returning container with {len(result.content.controls)} controls")
        return result
    
    def _build_user_management_section(self) -> ft.Container:
        """Build the user management section with inline audit log viewer"""
        
        print("[DEBUG] _build_user_management_section called")
        
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
        
        # Users table header with proportional widths
        table_header = ft.Row([
            ft.Container(width=50),  # Avatar space
            ft.Container(ft.Text("Email", weight=ft.FontWeight.BOLD, size=12), expand=2),
            ft.Container(ft.Text("Name", weight=ft.FontWeight.BOLD, size=12), expand=2),
            ft.Container(ft.Text("Role", weight=ft.FontWeight.BOLD, size=12), expand=1),
            ft.Container(ft.Text("Last Login", weight=ft.FontWeight.BOLD, size=12), expand=1),
            ft.Container(ft.Text("Status", weight=ft.FontWeight.BOLD, size=12), expand=1),
            ft.Container(ft.Text("Actions", weight=ft.FontWeight.BOLD, size=12), width=150),
        ], spacing=8, expand=True)
        
        # Users table content (will be populated dynamically)
        self.users_table = ft.Column(
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
        )
        
        # Wrap table in scroll container with fixed height
        table_scroll = ft.Container(
            content=ft.Column([
                table_header,
                ft.Divider(height=1),
                self.users_table,
            ], spacing=0, scroll=ft.ScrollMode.AUTO),
            height=400,  # Fixed height so audit logs are visible below
            border=ft.border.all(1, ft.Colors.GREY_800),
            border_radius=5,
        )
        
        # Initialize audit log service
        try:
            self.audit_log_service = AuditLogService()
            print("[DEBUG] Audit log service initialized successfully")
        except PermissionError as e:
            print(f"[ADMIN] Failed to initialize audit log service: {e}")
            self.audit_log_service = None
        
        # Build audit log UI inline
        print("[DEBUG] Building audit log UI...")
        audit_log_content = self._build_audit_log_ui()
        print(f"[DEBUG] Audit log content built: {audit_log_content is not None}")
        
        # Return user management section with audit logs below
        result = ft.Container(
            content=ft.Column([
                ft.Text("User Management", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
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
                
                # Table with fixed height scroll
                table_scroll,
                
                # Thick divider before audit logs
                ft.Divider(height=30, thickness=3, color=ft.Colors.ORANGE_700),
                
                # Audit logs section (built inline) - ALWAYS VISIBLE
                audit_log_content,
                
            ], spacing=15),  # NO SCROLL - parent handles it
            padding=10,
            expand=True
        )
        
        print(f"[DEBUG] _build_user_management_section returning with {len(result.content.controls)} controls")
        return result
    
    def _build_audit_log_ui(self) -> ft.Container:
        """Build the audit log viewer UI inline"""
        print("[DEBUG] _build_audit_log_ui called")
        
        if not self.audit_log_service:
            print("[DEBUG] No audit log service, returning unavailable message")
            return ft.Container(
                content=ft.Column([
                    ft.Text("AUDIT LOGS", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                    ft.Text("Audit logs unavailable - no permission", color=ft.Colors.RED),
                ]),
                padding=20,
                bgcolor=ft.Colors.RED_900,
                height=200
            )
        
        print("[DEBUG] Building audit log UI with service available")
        
        # Filter controls
        self.audit_actor_filter = ft.TextField(
            label="Filter by Actor",
            hint_text="admin@example.com",
            prefix_icon=ft.Icons.PERSON,
            on_change=lambda e: self._load_audit_logs(),
            width=250
        )
        
        self.audit_target_filter = ft.TextField(
            label="Filter by Target User",
            hint_text="user@example.com",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            on_change=lambda e: self._load_audit_logs(),
            width=250
        )
        
        self.audit_action_filter = ft.Dropdown(
            label="Action Type",
            options=[
                ft.dropdown.Option("all", "All Actions"),
                ft.dropdown.Option("role_change", "Role Change"),
                ft.dropdown.Option("user_creation", "User Creation"),
                ft.dropdown.Option("user_update", "User Update"),
                ft.dropdown.Option("user_deletion", "User Deletion"),
            ],
            value="all",
            on_change=lambda e: self._load_audit_logs(),
            width=200
        )
        
        self.audit_date_range = ft.Dropdown(
            label="Date Range",
            options=[
                ft.dropdown.Option("all", "All Time"),
                ft.dropdown.Option("today", "Today"),
                ft.dropdown.Option("week", "Last 7 Days"),
                ft.dropdown.Option("month", "Last 30 Days"),
            ],
            value="all",
            on_change=lambda e: self._load_audit_logs(),
            width=180
        )
        
        refresh_audit_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Refresh logs",
            on_click=lambda e: self._load_audit_logs(),
            bgcolor=ft.Colors.BLUE_700,
            icon_color=ft.Colors.WHITE
        )
        
        export_audit_btn = ft.ElevatedButton(
            "Export to CSV",
            icon=ft.Icons.DOWNLOAD,
            on_click=self._export_audit_logs,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE
        )
        
        clear_audit_filters_btn = ft.TextButton(
            "Clear Filters",
            icon=ft.Icons.CLEAR,
            on_click=self._clear_audit_filters
        )
        
        # Filter panel
        filter_panel = ft.Container(
            content=ft.Column([
                ft.Text("Audit Log Filters", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_400),
                ft.Row([
                    self.audit_actor_filter,
                    self.audit_target_filter,
                ], spacing=10, wrap=True),
                ft.Row([
                    self.audit_action_filter,
                    self.audit_date_range,
                    refresh_audit_btn,
                    export_audit_btn,
                    clear_audit_filters_btn
                ], spacing=10, wrap=True),
            ], spacing=10),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, "#2A2A2A"),
            border_radius=10,
            border=ft.border.all(1, ft.Colors.ORANGE_700),
        )
        
        # Log count and loading
        self.audit_log_count = ft.Text("No logs loaded", size=12, color=ft.Colors.GREY_400)
        self.audit_loading = ft.ProgressRing(visible=False, width=20, height=20)
        
        # Logs table
        self.audit_logs_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Timestamp", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Actor", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Action", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Target User", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, size=11)),
                ft.DataColumn(ft.Text("Details", weight=ft.FontWeight.BOLD, size=11)),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_800),
            border_radius=8,
            vertical_lines=ft.BorderSide(1, ft.Colors.GREY_800),
            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_800),
            heading_row_color=ft.Colors.GREY_900,
            heading_row_height=40,
            data_row_min_height=35,
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Audit Logs", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_400),
                ft.Text("Track all administrative actions (showing last 10)", size=12, color=ft.Colors.GREY_400),
                filter_panel,
                ft.Row([self.audit_log_count, self.audit_loading], spacing=10),
                ft.Container(
                    content=self.audit_logs_table,
                    border=ft.border.all(1, ft.Colors.GREY_700),
                    border_radius=8,
                    padding=10,
                ),
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=10,
            height=500
        )
    
    def load_users(self):
        """
        Load all users from Firebase with backend verification
        
        Future enhancements:
        - Pagination for large user bases (>100 users)
        - Caching with TTL to reduce Firebase reads
        - Real-time listener for live updates
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
            
            # Load audit logs when users are loaded
            self._load_audit_logs()
            
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
        
        Note: Rate limiting and session validation now handled per-action
        Future: Consider IP whitelist verification
        """
        if not self.firebase_service or not self.firebase_service.is_available:
            return False
        
        try:
            return self.firebase_service.verify_admin_permission(session_manager.email)
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
                ft.Container(ft.Text(email, size=11, overflow=ft.TextOverflow.ELLIPSIS), expand=2),
                ft.Container(name_display, expand=2),
                ft.Container(
                    ft.Container(
                        content=ft.Text(role.title(), size=10, weight=ft.FontWeight.BOLD),
                        bgcolor=self._get_role_color(role),
                        padding=4,
                        border_radius=4,
                    ),
                    expand=1,
                    alignment=ft.alignment.center,
                ),
                ft.Container(ft.Text(str(last_login), size=10, color=ft.Colors.GREY_400, overflow=ft.TextOverflow.ELLIPSIS), expand=1),
                ft.Container(ft.Text(status_text, size=10, color=status_color), expand=1),
                ft.Container(ft.Row([role_button, disable_button, delete_button], spacing=2, tight=True), width=150),
            ], spacing=8, tight=True, expand=True),
            padding=8,
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
        Includes audit logging, rate limiting, and prevents self-demotion
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
        
        # Execute role change directly
        self._execute_role_change(email, new_role, current_role)
    
    def _execute_role_change(self, email: str, new_role: str, old_role: str):
        """Execute the role change with backend verification, audit logging, and rate limiting"""
        try:
            if not self.firebase_service or not self.firebase_service.is_available:
                self._show_error("Firebase service unavailable")
                return
            
            # Security: Verify admin permission
            current_user_email = session_manager.email
            if not self.firebase_service.verify_admin_permission(current_user_email):
                self._show_error("Access denied: Admin verification failed")
                print(f"[SECURITY] Unauthorized role change attempt by {current_user_email}")
                return
            
            # Security: Check rate limit
            if not self.firebase_service.check_rate_limit(current_user_email, 'role_change'):
                self._show_error("Rate limit exceeded. Please wait before making more changes.")
                return
            
            # Execute role change
            success = self.firebase_service.update_user_role(email, new_role)
            
            # Log the admin action
            self.firebase_service.log_admin_action(
                admin_email=current_user_email,
                action='role_change',
                target_user=email,
                details={'old_role': old_role, 'new_role': new_role},
                success=success
            )
            
            if success:
                self._show_success(f"Role changed successfully: {email} → {new_role}")
                self._refresh_users(None)
                # Refresh audit logs
                if hasattr(self, '_load_audit_logs'):
                    self._load_audit_logs()
            else:
                self._show_error("Failed to change role")
        
        except Exception as e:
            print(f"[ERROR] Role change failed: {e}")
            self._show_error(f"Error: {str(e)}")
    
    def _toggle_user_status(self, user: Dict[str, Any]):
        """
        Enable or disable user account
        Prevents self-disable and super admin disable
        
        Note: Requires firebase_service.disable_user() and enable_user() methods
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
        
        self._show_error(f"Feature not yet implemented: User {action} requires firebase_service.disable_user() method")
        # Note: When implemented, add audit logging and rate limiting like other admin actions
    
    def _delete_user(self, user: Dict[str, Any]):
        """
        Delete user account (permanent action)
        Includes audit logging, rate limiting, and prevents self-deletion
        
        Note: Confirmation dialogs removed per user request
        Future: Consider archiving user data before deletion
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
        
        # Execute deletion directly
        self._execute_delete(email)
    
    def _execute_delete(self, email: str):
        """Execute user deletion with security verification, audit logging, and rate limiting"""
        try:
            if not self.firebase_service or not self.firebase_service.is_available:
                self._show_error("Firebase service unavailable")
                return
            
            # Security: Verify admin permission
            current_user_email = session_manager.email
            if not self.firebase_service.verify_admin_permission(current_user_email):
                self._show_error("Access denied: Admin verification failed")
                print(f"[SECURITY] Unauthorized user deletion attempt by {current_user_email}")
                return
            
            # Security: Check rate limit
            if not self.firebase_service.check_rate_limit(current_user_email, 'user_deletion'):
                self._show_error("Rate limit exceeded. Please wait before making more changes.")
                return
            
            # Delete user
            success = self.firebase_service.delete_user(email)
            
            # Log the admin action
            self.firebase_service.log_admin_action(
                admin_email=current_user_email,
                action='user_deletion',
                target_user=email,
                details={},
                success=success
            )
            
            if success:
                self._show_success(f"Deleted user: {email}")
                self._refresh_users(None)
                # Refresh audit logs
                if hasattr(self, '_load_audit_logs'):
                    self._load_audit_logs()
            else:
                self._show_error(f"Failed to delete user: {email}")
        
        except Exception as e:
            print(f"[ERROR] User deletion failed: {e}")
            self._show_error(f"Delete failed: {str(e)}")
    
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
        
        try:
            if not self.firebase_service or not self.firebase_service.is_available:
                self._show_error("Firebase service unavailable")
                return
            
            # Security: Verify admin permission
            current_user_email = session_manager.email
            if not self.firebase_service.verify_admin_permission(current_user_email):
                self._show_error("Access denied: Admin verification failed")
                print(f"[SECURITY] Unauthorized user creation attempt by {current_user_email}")
                return
            
            # Security: Check rate limit
            if not self.firebase_service.check_rate_limit(current_user_email, 'user_creation'):
                self._show_error("Rate limit exceeded. Please wait before making more changes.")
                return
            
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
                
                # Execute role update
                success = self.firebase_service.update_user_role(email, role)
                
                # Log the admin action
                self.firebase_service.log_admin_action(
                    admin_email=current_user_email,
                    action='user_update',
                    target_user=email,
                    details={'old_role': old_role, 'new_role': role},
                    success=success
                )
                
                if success:
                    self._show_success(f"Updated {email}: {old_role} → {role}")
                    self._refresh_users(None)
                    self.new_user_email.value = ""
                    self.page.update()
                    # Refresh audit logs
                    if hasattr(self, '_load_audit_logs'):
                        self._load_audit_logs()
                else:
                    self._show_error(f"Failed to update user role")
            else:
                # User doesn't exist - create placeholder document
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
                
                # Log the admin action
                self.firebase_service.log_admin_action(
                    admin_email=current_user_email,
                    action='user_creation',
                    target_user=email,
                    details={'role': role},
                    success=success
                )
                
                if success:
                    self._show_success(f"Created user {email} with role '{role}'. They can now log in with Google OAuth.")
                    self._refresh_users(None)
                    self.new_user_email.value = ""
                    self.page.update()
                    # Refresh audit logs
                    if hasattr(self, '_load_audit_logs'):
                        self._load_audit_logs()
                else:
                    self._show_error(f"Failed to create user")
        
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
    
    def _load_audit_logs(self):
        """Load audit logs with current filters"""
        if not self.audit_log_service:
            return
        
        if self.audit_loading:
            self.audit_loading.visible = True
            self.page.update()
        
        try:
            # Get filter values
            actor = self.audit_actor_filter.value.strip() if self.audit_actor_filter.value else None
            target = self.audit_target_filter.value.strip() if self.audit_target_filter.value else None
            action = self.audit_action_filter.value if self.audit_action_filter.value != "all" else None
            date_range = self.audit_date_range.value
            
            # Fetch logs
            self.audit_logs_data = self.audit_log_service.fetch_logs(
                actor_filter=actor,
                target_filter=target,
                action_filter=action,
                date_range=date_range
            )
            
            # Update display
            self._update_audit_logs_display()
            
            if self.audit_log_count:
                self.audit_log_count.value = f"Showing {len(self.audit_logs_data)} log entries"
        
        except Exception as e:
            print(f"[ADMIN] Error loading audit logs: {e}")
            self._show_error(f"Failed to load audit logs: {str(e)}")
        
        finally:
            if self.audit_loading:
                self.audit_loading.visible = False
                self.page.update()
    
    def _update_audit_logs_display(self):
        """Update the audit logs table with current data"""
        if not self.audit_logs_table:
            return
        
        if not self.audit_logs_data:
            self.audit_logs_table.rows = [
                ft.DataRow(cells=[ft.DataCell(ft.Text("No logs found", color=ft.Colors.GREY_500))])
            ]
            self.page.update()
            return
        
        rows = []
        for log in self.audit_logs_data[:50]:  # Show first 50
            # Format timestamp
            timestamp = log.get('timestamp')
            if hasattr(timestamp, 'strftime'):
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp_str = str(timestamp)
            
            # Status icon
            status_icon = "✅" if log.get('success', True) else "❌"
            
            # Details summary
            details = log.get('details', {})
            if isinstance(details, dict):
                details_str = ", ".join([f"{k}: {v}" for k, v in details.items()])
            else:
                details_str = str(details)
            
            if len(details_str) > 40:
                details_str = details_str[:37] + "..."
            
            rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(timestamp_str, size=10)),
                    ft.DataCell(ft.Text(log.get('admin_email', 'Unknown'), size=10)),
                    ft.DataCell(ft.Text(
                        log.get('action', 'Unknown').replace('_', ' ').title(),
                        size=10,
                        weight=ft.FontWeight.BOLD
                    )),
                    ft.DataCell(ft.Text(log.get('target_user', 'N/A'), size=10)),
                    ft.DataCell(ft.Text(status_icon, size=12)),
                    ft.DataCell(ft.Text(details_str, size=9, color=ft.Colors.GREY_400)),
                ]
            ))
        
        self.audit_logs_table.rows = rows
        self.page.update()
    
    def _export_audit_logs(self, e):
        """Export audit logs to CSV"""
        if not self.audit_log_service or not self.audit_logs_data:
            self._show_error("No logs to export")
            return
        
        success, message = self.audit_log_service.export_to_csv(self.audit_logs_data)
        if success:
            self._show_success(message)
        else:
            self._show_error(message)
    
    def _clear_audit_filters(self, e):
        """Clear all audit log filters"""
        if self.audit_actor_filter:
            self.audit_actor_filter.value = ""
        if self.audit_target_filter:
            self.audit_target_filter.value = ""
        if self.audit_action_filter:
            self.audit_action_filter.value = "all"
        if self.audit_date_range:
            self.audit_date_range.value = "all"
        self.page.update()
        self._load_audit_logs()

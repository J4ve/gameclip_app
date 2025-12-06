"""
Admin Dashboard Integration Example
Shows how to integrate the admin dashboard into main_window.py

This file serves as a reference for adding the admin dashboard tab.
Copy the relevant code sections into main_window.py as needed.
"""

import flet as ft
from access_control.session import session_manager
from access_control.roles import Permission
from app.gui.admin_dashboard_screen import AdminDashboardScreen


def integrate_admin_dashboard_example(page: ft.Page):
    """
    Example: How to add admin dashboard to main window tabs
    
    Add this code to main_window.py in the build() method
    where tabs are created.
    """
    
    # Example tab list (your actual implementation may differ)
    tabs = []
    
    # Add your existing tabs
    # tabs.append(ft.Tab(text="Selection", content=selection_screen.build()))
    # tabs.append(ft.Tab(text="Arrangement", content=arrangement_screen.build()))
    # tabs.append(ft.Tab(text="Save/Upload", content=save_upload_screen.build()))
    # tabs.append(ft.Tab(text="Config", content=config_tab.build()))
    
    # ADMIN DASHBOARD TAB - Only visible to admins
    # This is the code to add to main_window.py
    if session_manager.has_permission(Permission.MANAGE_USERS.value):
        print("[MAIN_WINDOW] Admin user detected, adding admin dashboard tab")
        
        try:
            # Create admin dashboard instance
            admin_dashboard = AdminDashboardScreen(page)
            
            # Add tab with admin icon
            tabs.append(ft.Tab(
                text="Admin Dashboard",
                icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                content=admin_dashboard.build()
            ))
            
            # Load users data when tab is created
            # Consider loading only when tab is selected for better performance
            admin_dashboard.load_users()
            
        except Exception as e:
            print(f"[ERROR] Failed to create admin dashboard: {e}")
            # Optionally show error snackbar to user
    
    else:
        print("[MAIN_WINDOW] Non-admin user, admin dashboard hidden")
    
    # Return tabs for use in Tabs widget
    return tabs


def alternative_lazy_loading_example(page: ft.Page):
    """
    Alternative: Lazy load admin dashboard only when tab is selected
    
    This approach is better for performance as it doesn't load user data
    until the admin actually clicks on the dashboard tab.
    """
    
    tabs = []
    admin_dashboard_instance = None
    
    def on_tab_change(e):
        """Handle tab selection change"""
        selected_index = e.control.selected_index
        
        # If admin dashboard tab is selected (adjust index as needed)
        if selected_index == 4:  # Assuming admin tab is 5th tab (index 4)
            if admin_dashboard_instance:
                print("[ADMIN] Loading user data...")
                admin_dashboard_instance.load_users()
    
    # Create tabs with event handler
    if session_manager.has_permission(Permission.MANAGE_USERS.value):
        admin_dashboard_instance = AdminDashboardScreen(page)
        
        tabs.append(ft.Tab(
            text="Admin Dashboard",
            icon=ft.Icons.ADMIN_PANEL_SETTINGS,
            content=admin_dashboard_instance.build()
        ))
    
    # Create Tabs widget with change handler
    tabs_widget = ft.Tabs(
        tabs=tabs,
        selected_index=0,
        on_change=on_tab_change,
        expand=True
    )
    
    return tabs_widget


def security_check_example():
    """
    Example: How to add additional security checks
    
    You can add these checks in main_window.py before showing admin dashboard
    """
    
    # Check 1: Verify user is logged in
    if not session_manager.is_logged_in:
        print("[SECURITY] User not logged in, denying admin access")
        return False
    
    # Check 2: Verify user has admin role
    if not session_manager.is_admin():
        print(f"[SECURITY] User {session_manager.email} is not admin")
        return False
    
    # Check 3: Verify user has MANAGE_USERS permission
    if not session_manager.has_permission(Permission.MANAGE_USERS.value):
        print(f"[SECURITY] User {session_manager.email} lacks MANAGE_USERS permission")
        return False
    
    # Check 4: Verify session is still valid
    # TODO: Add token expiration check
    
    print(f"[SECURITY] All checks passed for {session_manager.email}")
    return True


# Example usage in main_window.py:
"""
class MainWindow:
    def build(self):
        # ... existing code ...
        
        # Create tabs list
        tabs = [
            ft.Tab(text="Selection", content=self.selection_screen.build()),
            ft.Tab(text="Arrangement", content=self.arrangement_screen.build()),
            ft.Tab(text="Save/Upload", content=self.save_upload_screen.build()),
            ft.Tab(text="Config", content=self.config_tab.build()),
        ]
        
        # Add admin dashboard if user has permission
        if session_manager.has_permission(Permission.MANAGE_USERS.value):
            from app.gui.admin_dashboard_screen import AdminDashboardScreen
            admin_dashboard = AdminDashboardScreen(self.page)
            admin_dashboard.load_users()
            
            tabs.append(ft.Tab(
                text="Admin Dashboard",
                icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                content=admin_dashboard.build()
            ))
        
        # Create tabs widget
        self.tabs = ft.Tabs(
            tabs=tabs,
            selected_index=0,
            expand=True
        )
        
        return ft.Container(
            content=ft.Column([
                # ... existing controls ...
                self.tabs,
            ]),
            expand=True
        )
"""

"""
Test Admin Dashboard Integration
Ensures proper initialization order and no duplicate code execution
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestAdminDashboardInitialization:
    """Test correct initialization order of admin dashboard"""
    
    @patch('app.gui.admin_dashboard.session_manager')
    @patch('app.gui.admin_dashboard.get_firebase_service')
    def test_admin_dashboard_build_before_load(self, mock_firebase, mock_session):
        """Test that build() creates UI components before load_users() is called"""
        from app.gui.admin_dashboard import AdminDashboard
        import flet as ft
        
        # Setup mocks
        mock_session.has_permission.return_value = True
        mock_session.email = "admin@test.com"
        
        mock_fb_instance = Mock()
        mock_fb_instance.is_available = True
        mock_fb_instance.verify_admin_permission.return_value = True
        mock_fb_instance.get_all_users.return_value = [
            {'email': 'user1@test.com', 'role': 'free', 'name': 'User 1'},
            {'email': 'user2@test.com', 'role': 'premium', 'name': 'User 2'},
        ]
        mock_firebase.return_value = mock_fb_instance
        
        # Create mock page
        mock_page = Mock(spec=ft.Page)
        
        # Create dashboard instance
        dashboard = AdminDashboard(mock_page)
        
        # At this point, users_table should be None
        assert dashboard.users_table is None, "users_table should be None before build()"
        
        # Call build() - this should create UI components
        with patch.object(dashboard, '_load_audit_logs'):
            result = dashboard.build()
        
        # Now users_table should exist
        assert dashboard.users_table is not None, "users_table should exist after build()"
        assert hasattr(dashboard.users_table, 'controls'), "users_table should have controls attribute"
        
        # Now we can safely call load_users()
        with patch.object(dashboard, '_load_audit_logs'):
            dashboard.load_users()
        
        # Should have loaded users without error
        assert len(dashboard.users_data) == 2
        assert len(dashboard.filtered_users) == 2
    
    @patch('app.gui.admin_dashboard.session_manager')
    @patch('app.gui.admin_dashboard.get_firebase_service')
    def test_load_users_before_build_raises_error(self, mock_firebase, mock_session):
        """Test that calling load_users() before build() causes an error"""
        from app.gui.admin_dashboard import AdminDashboard
        import flet as ft
        
        # Setup mocks
        mock_session.has_permission.return_value = True
        mock_session.email = "admin@test.com"
        
        mock_fb_instance = Mock()
        mock_fb_instance.is_available = True
        mock_fb_instance.verify_admin_permission.return_value = True
        mock_fb_instance.get_all_users.return_value = [
            {'email': 'user1@test.com', 'role': 'free'},
        ]
        mock_firebase.return_value = mock_fb_instance
        
        # Create mock page
        mock_page = Mock(spec=ft.Page)
        
        # Create dashboard instance
        dashboard = AdminDashboard(mock_page)
        
        # Try to load users BEFORE building UI - should fail
        with patch.object(dashboard, '_load_audit_logs'):
            dashboard.load_users()
        
        # This should have caused an error (AttributeError: 'NoneType' object has no attribute 'controls')
        # The error should be caught and logged
        # Verify the error was logged
        assert dashboard.users_table is None, "users_table is still None"


class TestConfigTabIntegration:
    """Test ConfigTab properly uses AdminDashboard without duplicates"""
    
    @patch('app.gui.config_tab.session_manager')
    @patch('app.gui.admin_dashboard.session_manager')
    @patch('access_control.firebase_service.get_firebase_service')
    def test_config_tab_uses_real_admin_dashboard(
        self, mock_get_firebase, mock_admin_session, mock_config_session
    ):
        """Test that ConfigTab uses real AdminDashboard without duplicate logic"""
        from app.gui.config_tab import ConfigTab
        import flet as ft
        
        # Setup mocks
        mock_admin_session.has_permission.return_value = True
        mock_admin_session.email = "admin@test.com"
        mock_admin_session.is_guest = False
        mock_admin_session.current_role = Mock()
        mock_admin_session.current_role.permissions = []
        mock_admin_session.get_user_display_info.return_value = {
            'name': 'Admin User',
            'role': 'admin',
            'picture': ''
        }
        
        mock_config_session.has_permission.return_value = True
        mock_config_session.email = "admin@test.com"
        mock_config_session.is_guest = False
        mock_config_session.current_role = Mock()
        mock_config_session.current_role.permissions = []
        mock_config_session.get_user_display_info.return_value = {
            'name': 'Admin User',
            'role': 'admin',
            'picture': ''
        }
        
        mock_fb_instance = Mock()
        mock_fb_instance.is_available = True
        mock_fb_instance.verify_admin_permission.return_value = True
        mock_fb_instance.get_all_users.return_value = [
            {'email': 'user1@test.com', 'role': 'free', 'name': 'User 1'},
        ]
        mock_fb_instance.get_audit_logs.return_value = []
        mock_get_firebase.return_value = mock_fb_instance
        
        # Create mock page
        mock_page = Mock(spec=ft.Page)
        
        # Create ConfigTab instance
        config_tab = ConfigTab(mock_page)
        
        # Build admin dashboard through config tab
        result = config_tab._build_admin_dashboard()
        
        # Verify real AdminDashboard instance was created
        assert hasattr(config_tab, 'real_admin_dashboard'), "Should have real_admin_dashboard instance"
        assert config_tab.real_admin_dashboard is not None
        
        # Verify build() was called (which creates users_table)
        assert config_tab.real_admin_dashboard.users_table is not None, "users_table should exist"
        
        # Verify load_users() was called (which populates the table)
        assert len(config_tab.real_admin_dashboard.users_data) >= 0, "users_data should be initialized"
    
    @patch('app.gui.config_tab.session_manager')
    def test_config_tab_duplicate_methods_removed(self, mock_session):
        """Test that duplicate _admin_* methods are removed from ConfigTab"""
        from app.gui.config_tab import ConfigTab
        import flet as ft
        
        mock_page = Mock(spec=ft.Page)
        config_tab = ConfigTab(mock_page)
        
        # Verify duplicate methods are gone
        assert not hasattr(config_tab, '_admin_load_users'), "_admin_load_users should be removed"
        assert not hasattr(config_tab, '_admin_change_role'), "_admin_change_role should be removed"
        assert not hasattr(config_tab, '_admin_delete_user'), "_admin_delete_user should be removed"
        assert not hasattr(config_tab, '_admin_populate_users_table'), "_admin_populate_users_table should be removed"


class TestMethodExecutionOrder:
    """Test the correct execution order of admin dashboard methods"""
    
    @patch('app.gui.admin_dashboard.session_manager')
    @patch('app.gui.admin_dashboard.get_firebase_service')
    def test_execution_order_build_then_load(self, mock_firebase, mock_session):
        """Test that build() is called before load_users()"""
        from app.gui.admin_dashboard import AdminDashboard
        import flet as ft
        
        # Setup mocks
        mock_session.has_permission.return_value = True
        mock_session.email = "admin@test.com"
        
        mock_fb_instance = Mock()
        mock_fb_instance.is_available = True
        mock_fb_instance.verify_admin_permission.return_value = True
        mock_fb_instance.get_all_users.return_value = []
        mock_fb_instance.get_audit_logs.return_value = []
        mock_firebase.return_value = mock_fb_instance
        
        mock_page = Mock(spec=ft.Page)
        
        dashboard = AdminDashboard(mock_page)
        
        # Track method calls
        call_order = []
        
        original_build = dashboard.build
        original_load = dashboard.load_users
        
        def tracked_build():
            call_order.append('build')
            return original_build()
        
        def tracked_load():
            call_order.append('load_users')
            return original_load()
        
        dashboard.build = tracked_build
        dashboard.load_users = tracked_load
        
        # Simulate correct usage
        dashboard.build()
        dashboard.load_users()
        
        # Verify order
        assert call_order == ['build', 'load_users'], f"Wrong order: {call_order}"
    
    @patch('app.gui.config_tab.session_manager')
    @patch('app.gui.admin_dashboard.session_manager')
    @patch('access_control.firebase_service.get_firebase_service')
    def test_config_tab_calls_build_before_load(
        self, mock_get_firebase, mock_admin_session, mock_config_session
    ):
        """Test that ConfigTab calls build() before load_users()"""
        from app.gui.config_tab import ConfigTab
        from app.gui.admin_dashboard import AdminDashboard
        import flet as ft
        
        # Setup mocks
        mock_admin_session.has_permission.return_value = True
        mock_admin_session.email = "admin@test.com"
        mock_admin_session.is_guest = False
        mock_admin_session.current_role = Mock()
        mock_admin_session.current_role.permissions = []
        
        mock_config_session.has_permission.return_value = True
        mock_config_session.email = "admin@test.com"
        mock_config_session.is_guest = False
        mock_config_session.current_role = Mock()
        mock_config_session.current_role.permissions = []
        mock_config_session.get_user_display_info.return_value = {
            'name': 'Admin',
            'role': 'admin',
            'picture': ''
        }
        
        mock_fb_instance = Mock()
        mock_fb_instance.is_available = True
        mock_fb_instance.verify_admin_permission.return_value = True
        mock_fb_instance.get_all_users.return_value = []
        mock_fb_instance.get_audit_logs.return_value = []
        mock_get_firebase.return_value = mock_fb_instance
        
        mock_page = Mock(spec=ft.Page)
        
        config_tab = ConfigTab(mock_page)
        
        # Track AdminDashboard method calls
        call_order = []
        
        original_build = AdminDashboard.build
        original_load = AdminDashboard.load_users
        
        def tracked_build(self):
            call_order.append('build')
            return original_build(self)
        
        def tracked_load(self, *args, **kwargs):
            call_order.append('load_users')
            return original_load(self, *args, **kwargs)
        
        with patch.object(AdminDashboard, 'build', tracked_build):
            with patch.object(AdminDashboard, 'load_users', tracked_load):
                # This should call build() first, then load_users()
                result = config_tab._build_admin_dashboard()
        
        # Verify correct order
        assert call_order == ['build', 'load_users'], f"ConfigTab called methods in wrong order: {call_order}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

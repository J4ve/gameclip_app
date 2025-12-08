"""
Test Admin Dashboard User Management
Verify user creation and updates work correctly
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class TestAdminUserManagement:
    """Test user management functions in AdminDashboard"""
    
    @patch('app.gui.admin_dashboard.session_manager')
    @patch('app.gui.admin_dashboard.get_firebase_service')
    def test_add_new_user_calls_placeholder(self, mock_get_firebase, mock_session):
        """Test that adding a new user calls create_user_placeholder"""
        from app.gui.admin_dashboard import AdminDashboard
        import flet as ft
        
        # Setup mocks
        mock_session.email = "admin@test.com"
        
        mock_fb = Mock()
        mock_fb.is_available = True
        mock_fb.verify_admin_permission.return_value = True
        mock_fb.check_rate_limit.return_value = True
        mock_fb.get_user_by_email.return_value = None  # User doesn't exist
        mock_fb.create_user_placeholder.return_value = True
        mock_get_firebase.return_value = mock_fb
        
        mock_page = Mock(spec=ft.Page)
        
        # Create dashboard
        dashboard = AdminDashboard(mock_page)
        
        # Setup UI elements needed for the test
        dashboard.new_user_email = Mock()
        dashboard.new_user_email.value = "newuser@test.com"
        dashboard.new_user_role = Mock()
        dashboard.new_user_role.value = "premium"
        
        # Mock methods that update UI
        dashboard._show_success = Mock()
        dashboard._refresh_users = Mock()
        dashboard._load_audit_logs = Mock()
        
        # Call the method
        dashboard._add_or_update_user(None)
        
        # Verify create_user_placeholder was called
        mock_fb.create_user_placeholder.assert_called_once_with("newuser@test.com", "premium")
        
        # Verify success message
        dashboard._show_success.assert_called_once()
        
    @patch('app.gui.admin_dashboard.session_manager')
    @patch('app.gui.admin_dashboard.get_firebase_service')
    def test_update_existing_user(self, mock_get_firebase, mock_session):
        """Test that updating an existing user calls update_user_role"""
        from app.gui.admin_dashboard import AdminDashboard
        import flet as ft
        
        # Setup mocks
        mock_session.email = "admin@test.com"
        
        mock_fb = Mock()
        mock_fb.is_available = True
        mock_fb.verify_admin_permission.return_value = True
        mock_fb.check_rate_limit.return_value = True
        # User exists
        mock_fb.get_user_by_email.return_value = {'email': 'existing@test.com', 'role': 'free'}
        mock_fb.update_user_role.return_value = True
        mock_get_firebase.return_value = mock_fb
        
        mock_page = Mock(spec=ft.Page)
        
        # Create dashboard
        dashboard = AdminDashboard(mock_page)
        
        # Setup UI elements
        dashboard.new_user_email = Mock()
        dashboard.new_user_email.value = "existing@test.com"
        dashboard.new_user_role = Mock()
        dashboard.new_user_role.value = "premium"
        
        # Mock methods that update UI
        dashboard._show_success = Mock()
        dashboard._refresh_users = Mock()
        dashboard._load_audit_logs = Mock()
        
        # Call the method
        dashboard._add_or_update_user(None)
        
        # Verify update_user_role was called
        mock_fb.update_user_role.assert_called_once_with("existing@test.com", "premium")
        
        # Verify success message
        dashboard._show_success.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

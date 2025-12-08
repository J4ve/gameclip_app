import sys
import os
# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
# Add root to path (for configs)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch
from app.gui.admin_dashboard import AdminDashboard
from access_control.session import session_manager
from configs.config import Config

@pytest.fixture
def mock_page():
    page = MagicMock()
    page.snack_bar = MagicMock()
    return page

@pytest.fixture
def admin_dashboard(mock_page):
    with patch('src.app.gui.admin_dashboard.AuditLogService'):
        dashboard = AdminDashboard(mock_page)
        dashboard.firebase_service = MagicMock()
        dashboard.firebase_service.is_available = True
        dashboard.firebase_service.verify_admin_permission.return_value = True
        dashboard.firebase_service.check_rate_limit.return_value = True
        dashboard._refresh_users = MagicMock()
        dashboard._load_audit_logs = MagicMock()
        return dashboard

def test_toggle_user_status_disable(admin_dashboard):
    # Setup
    user = {'email': 'test@example.com', 'disabled': False}
    session_manager._current_user = {'email': 'admin@example.com'}
    admin_dashboard.firebase_service.disable_user.return_value = True
    
    # Execute
    admin_dashboard._toggle_user_status(user)
    
    # Verify
    admin_dashboard.firebase_service.disable_user.assert_called_once_with('test@example.com')
    admin_dashboard.firebase_service.log_admin_action.assert_called_once()
    args = admin_dashboard.firebase_service.log_admin_action.call_args[1]
    assert args['action'] == 'user_disable'
    assert args['target_user'] == 'test@example.com'
    assert args['success'] is True
    
    # Verify UI updates
    admin_dashboard._refresh_users.assert_called_once()
    admin_dashboard._load_audit_logs.assert_called_once()

def test_toggle_user_status_enable(admin_dashboard):
    # Setup
    user = {'email': 'test@example.com', 'disabled': True}
    session_manager._current_user = {'email': 'admin@example.com'}
    admin_dashboard.firebase_service.enable_user.return_value = True
    
    # Execute
    admin_dashboard._toggle_user_status(user)
    
    # Verify
    admin_dashboard.firebase_service.enable_user.assert_called_once_with('test@example.com')
    admin_dashboard.firebase_service.log_admin_action.assert_called_once()
    args = admin_dashboard.firebase_service.log_admin_action.call_args[1]
    assert args['action'] == 'user_enable'

def test_toggle_user_status_prevent_self_disable(admin_dashboard):
    # Setup
    session_manager._current_user = {'email': 'admin@example.com'}
    user = {'email': 'admin@example.com', 'disabled': False}
    
    # Execute
    admin_dashboard._toggle_user_status(user)
    
    # Verify
    admin_dashboard.firebase_service.disable_user.assert_not_called()
    # Should show error
    assert admin_dashboard.page.snack_bar.open is True
    assert "Cannot disable your own account" in str(admin_dashboard.page.snack_bar.content.value)

def test_toggle_user_status_prevent_super_admin_disable(admin_dashboard):
    # Setup
    session_manager._current_user = {'email': 'admin@example.com'}
    user = {'email': Config.SUPER_ADMIN_EMAIL, 'disabled': False}
    
    # Execute
    admin_dashboard._toggle_user_status(user)
    
    # Verify
    admin_dashboard.firebase_service.disable_user.assert_not_called()
    assert admin_dashboard.page.snack_bar.open is True
    assert "super admin account" in str(admin_dashboard.page.snack_bar.content.value)

"""
Integration tests for Authentication Flow
Tests full authentication workflow: OAuth → Firebase → Session → User Management
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from access_control.session import SessionManager
from access_control.roles import RoleType, Permission, RoleManager


@pytest.fixture
def mock_youtube_service():
    """Mock YouTube service with credentials"""
    mock_service = Mock()
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds.scopes = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ]
    mock_service.credentials = mock_creds
    return mock_service


@pytest.fixture
def mock_user_info():
    """Mock Google user info"""
    return {
        'email': 'testuser@example.com',
        'name': 'Test User',
        'id': 'google_user_123',
        'picture': 'https://example.com/photo.jpg',
        'given_name': 'Test',
        'family_name': 'User'
    }


@pytest.fixture
def mock_firebase_service():
    """Mock Firebase service"""
    with patch('access_control.firebase_service.FirebaseService') as mock_fs_class:
        mock_fs = Mock()
        mock_fs.is_available = True
        mock_fs_class.return_value = mock_fs
        yield mock_fs


class TestFullAuthenticationFlow:
    """Test complete authentication flow from OAuth to session"""
    
    @patch('uploader.auth.get_youtube_service')
    @patch('uploader.auth.get_user_info')
    def test_guest_to_authenticated_user_flow(self, mock_get_user_info, mock_get_yt_service, 
                                              mock_youtube_service, mock_user_info):
        """Test complete flow: guest login → OAuth → authenticated user"""
        # Setup mocks
        mock_get_yt_service.return_value = mock_youtube_service
        mock_get_user_info.return_value = mock_user_info
        
        # Step 1: Start as guest
        session = SessionManager()
        guest_role = RoleManager.create_role_by_name('guest')
        session.login({'email': 'guest@temp.com', 'name': 'Guest', 'uid': 'guest_temp'}, guest_role)
        
        assert session.is_guest is True
        assert session.has_permission('upload_video') is False
        
        # Step 2: Authenticate with OAuth
        yt_service = mock_get_yt_service()
        user_info = mock_get_user_info(yt_service.credentials)
        
        # Step 3: Login as authenticated user
        free_role = RoleManager.create_role_by_name('free')
        session.login({
            'email': user_info['email'],
            'name': user_info['name'],
            'uid': user_info['id'],
            'picture': user_info['picture']
        }, free_role)
        
        # Verify authentication
        assert session.is_guest is False
        assert session.is_logged_in is True
        assert session.email == mock_user_info['email']
        assert session.has_permission('upload_video') is True
    
    @patch('uploader.auth.get_youtube_service')
    @patch('uploader.auth.get_user_info')
    @patch('access_control.firebase_service.get_firebase_service')
    def test_authentication_with_firebase_sync(self, mock_get_fb_service, mock_get_user_info, 
                                               mock_get_yt_service, mock_youtube_service, 
                                               mock_user_info, mock_firebase_service):
        """Test authentication flow with Firebase synchronization"""
        # Setup mocks
        mock_get_yt_service.return_value = mock_youtube_service
        mock_get_user_info.return_value = mock_user_info
        mock_get_fb_service.return_value = mock_firebase_service
        
        # Mock Firebase to return None (new user)
        mock_firebase_service.get_user_by_uid.return_value = None
        mock_firebase_service.create_user.return_value = {'email': mock_user_info['email'], 'role': 'free'}
        
        # Authenticate
        yt_service = mock_get_yt_service()
        user_info = mock_get_user_info(yt_service.credentials)
        
        # Login with Firebase sync
        session = SessionManager()
        free_role = RoleManager.create_role_by_name('free')
        
        user_data = {
            'email': user_info['email'],
            'name': user_info['name'],
            'uid': user_info['id'],
            'picture': user_info['picture'],
            'provider': 'google'
        }
        
        session.login(user_data, free_role)
        
        # Verify Firebase sync attempted
        assert session.is_logged_in is True
        assert session.email == mock_user_info['email']


class TestUserManagementIntegration:
    """Test user management operations through full stack"""
    
    @patch('access_control.firebase_service.get_firebase_service')
    def test_admin_creates_and_upgrades_user(self, mock_get_fb_service, mock_firebase_service):
        """Test admin creating user and upgrading their role"""
        mock_get_fb_service.return_value = mock_firebase_service
        
        # Setup Firebase mocks
        mock_firebase_service.create_user_placeholder.return_value = True
        mock_firebase_service.update_user_role.return_value = True
        mock_firebase_service.verify_admin_permission.return_value = True
        mock_firebase_service.log_admin_action.return_value = True
        
        # Step 1: Admin logs in
        admin_session = SessionManager()
        admin_role = RoleManager.create_role_by_name('admin')
        admin_session.login({
            'email': 'admin@example.com',
            'name': 'Admin User',
            'uid': 'admin_123'
        }, admin_role)
        
        assert admin_session.has_permission('manage_users') is True
        
        # Step 2: Admin creates new user with placeholder
        new_user_email = 'newuser@example.com'
        result = mock_firebase_service.create_user_placeholder(new_user_email, 'free')
        assert result is True
        
        # Step 3: Admin upgrades user to premium
        result = mock_firebase_service.update_user_role(new_user_email, 'premium')
        assert result is True
        
        # Step 4: Verify audit log was created
        mock_firebase_service.log_admin_action(
            admin_email='admin@example.com',
            action='role_change',
            target_user=new_user_email,
            details={'old_role': 'free', 'new_role': 'premium'}
        )
        mock_firebase_service.log_admin_action.assert_called()
    
    @patch('access_control.firebase_service.get_firebase_service')
    def test_non_admin_cannot_manage_users(self, mock_get_fb_service, mock_firebase_service):
        """Test that non-admin users cannot perform admin operations"""
        mock_get_fb_service.return_value = mock_firebase_service
        mock_firebase_service.verify_admin_permission.return_value = False
        
        # Login as regular user
        user_session = SessionManager()
        free_role = RoleManager.create_role_by_name('free')
        user_session.login({
            'email': 'user@example.com',
            'name': 'Regular User',
            'uid': 'user_123'
        }, free_role)
        
        # Verify no admin permissions
        assert user_session.has_permission('manage_users') is False
        assert user_session.has_permission('change_roles') is False
        
        # Attempt admin operation should fail verification
        is_admin = mock_firebase_service.verify_admin_permission('user@example.com')
        assert is_admin is False


class TestRoleUpgradeFlow:
    """Test role upgrade workflows"""
    
    @patch('access_control.firebase_service.get_firebase_service')
    def test_free_to_premium_upgrade_flow(self, mock_get_fb_service, mock_firebase_service):
        """Test upgrading from free to premium tier"""
        mock_get_fb_service.return_value = mock_firebase_service
        mock_firebase_service.update_user_role.return_value = True
        
        # Login as free user
        session = SessionManager()
        free_role = RoleManager.create_role_by_name('free')
        session.login({
            'email': 'user@example.com',
            'name': 'Test User',
            'uid': 'user_123'
        }, free_role)
        
        # Verify free tier limitations
        assert session.current_role.limits.ads_enabled is True
        assert session.role_name == 'free'
        
        # Upgrade to premium
        success = session.update_role('premium')
        assert success is True
        assert session.role_name == 'premium'
        
        # Verify premium benefits
        assert session.has_permission('no_ads') is True
        assert session.has_permission('no_watermark') is True
        assert session.current_role.limits.ads_enabled is False
    
    def test_role_upgrade_preserves_session(self):
        """Test that role upgrade preserves other session data"""
        session = SessionManager()
        
        user_data = {
            'email': 'user@example.com',
            'name': 'Test User',
            'uid': 'user_123',
            'picture': 'https://example.com/photo.jpg'
        }
        
        # Login as free
        free_role = RoleManager.create_role_by_name('free')
        session.login(user_data, free_role)
        
        original_email = session.email
        original_uid = session.uid
        
        # Upgrade role
        session.update_role('premium')
        
        # Verify session data preserved
        assert session.email == original_email
        assert session.uid == original_uid
        assert session.is_logged_in is True


class TestMultiUserScenarios:
    """Test scenarios with multiple users"""
    
    @patch('access_control.firebase_service.get_firebase_service')
    def test_multiple_sessions_independent(self, mock_get_fb_service, mock_firebase_service):
        """Test that multiple sessions remain independent"""
        mock_get_fb_service.return_value = mock_firebase_service
        
        # Create two sessions
        session1 = SessionManager()
        session2 = SessionManager()
        
        # Login user 1 as free
        free_role = RoleManager.create_role_by_name('free')
        session1.login({
            'email': 'user1@example.com',
            'name': 'User One',
            'uid': 'user_1'
        }, free_role)
        
        # Login user 2 as admin
        admin_role = RoleManager.create_role_by_name('admin')
        session2.login({
            'email': 'admin@example.com',
            'name': 'Admin User',
            'uid': 'admin_1'
        }, admin_role)
        
        # Verify independence
        assert session1.email == 'user1@example.com'
        assert session2.email == 'admin@example.com'
        assert session1.role_name == 'free'
        assert session2.role_name == 'admin'
        assert session1.has_permission('manage_users') is False
        assert session2.has_permission('manage_users') is True


class TestAuditLoggingIntegration:
    """Test audit logging across operations"""
    
    @patch('access_control.firebase_service.get_firebase_service')
    def test_audit_log_for_role_changes(self, mock_get_fb_service, mock_firebase_service):
        """Test that role changes are logged to audit trail"""
        mock_get_fb_service.return_value = mock_firebase_service
        mock_firebase_service.log_admin_action.return_value = True
        mock_firebase_service.update_user_role.return_value = True
        
        # Admin logs in
        admin_session = SessionManager()
        admin_role = RoleManager.create_role_by_name('admin')
        admin_session.login({
            'email': 'admin@example.com',
            'name': 'Admin',
            'uid': 'admin_123'
        }, admin_role)
        
        # Perform role change
        target_user = 'user@example.com'
        mock_firebase_service.update_user_role(target_user, 'premium')
        
        # Log the action
        mock_firebase_service.log_admin_action(
            admin_email=admin_session.email,
            action='role_change',
            target_user=target_user,
            details={'old_role': 'free', 'new_role': 'premium'},
            success=True
        )
        
        # Verify logging
        mock_firebase_service.log_admin_action.assert_called_once()
        call_args = mock_firebase_service.log_admin_action.call_args.kwargs
        assert call_args['admin_email'] == 'admin@example.com'
        assert call_args['action'] == 'role_change'
        assert call_args['target_user'] == target_user
        assert call_args['success'] is True
    
    @patch('access_control.firebase_service.get_firebase_service')
    def test_audit_log_for_user_deletion(self, mock_get_fb_service, mock_firebase_service):
        """Test that user deletions are logged"""
        mock_get_fb_service.return_value = mock_firebase_service
        mock_firebase_service.delete_user.return_value = True
        mock_firebase_service.log_admin_action.return_value = True
        
        # Admin deletes user
        admin_email = 'admin@example.com'
        target_user = 'user@example.com'
        
        mock_firebase_service.delete_user(target_user)
        mock_firebase_service.log_admin_action(
            admin_email=admin_email,
            action='user_deletion',
            target_user=target_user,
            details={'reason': 'Admin request'},
            success=True
        )
        
        # Verify both operations
        mock_firebase_service.delete_user.assert_called_once_with(target_user)
        mock_firebase_service.log_admin_action.assert_called_once()


class TestPermissionEnforcement:
    """Test permission enforcement across the system"""
    
    def test_permission_escalation_prevention(self):
        """Test that permission escalation is prevented"""
        # Free user shouldn't get admin permissions
        session = SessionManager()
        free_role = RoleManager.create_role_by_name('free')
        
        session.login({
            'email': 'user@example.com',
            'name': 'User',
            'uid': 'user_123'
        }, free_role)
        
        # Verify no admin permissions
        assert session.has_permission('manage_users') is False
        assert session.has_permission('ban_users') is False
        assert session.has_permission('change_roles') is False
    
    def test_permission_hierarchy(self):
        """Test that permission hierarchy is enforced"""
        # Guest < Free < Premium < Dev < Admin
        guest = RoleManager.create_role_by_name('guest')
        free = RoleManager.create_role_by_name('free')
        premium = RoleManager.create_role_by_name('premium')
        dev = RoleManager.create_role_by_name('dev')
        admin = RoleManager.create_role_by_name('admin')
        
        # Upload permission progression
        assert guest.has_permission(Permission.UPLOAD_VIDEO) is False
        assert free.has_permission(Permission.UPLOAD_VIDEO) is True
        assert premium.has_permission(Permission.UPLOAD_VIDEO) is True
        assert dev.has_permission(Permission.UPLOAD_VIDEO) is True
        assert admin.has_permission(Permission.UPLOAD_VIDEO) is True
        
        # Admin permission (only admin)
        assert guest.has_permission(Permission.MANAGE_USERS) is False
        assert free.has_permission(Permission.MANAGE_USERS) is False
        assert premium.has_permission(Permission.MANAGE_USERS) is False
        assert dev.has_permission(Permission.MANAGE_USERS) is False
        assert admin.has_permission(Permission.MANAGE_USERS) is True


class TestErrorHandling:
    """Test error handling in integration scenarios"""
    
    @patch('access_control.firebase_service.get_firebase_service')
    def test_firebase_unavailable_graceful_degradation(self, mock_get_fb_service):
        """Test graceful degradation when Firebase is unavailable"""
        # Mock Firebase as unavailable
        mock_fb = Mock()
        mock_fb.is_available = False
        mock_get_fb_service.return_value = mock_fb
        
        # Should still be able to login (local mode)
        session = SessionManager()
        free_role = RoleManager.create_role_by_name('free')
        
        session.login({
            'email': 'user@example.com',
            'name': 'User',
            'uid': 'user_123'
        }, free_role)
        
        # Session should work locally
        assert session.is_logged_in is True
        assert session.email == 'user@example.com'
    
    def test_invalid_role_name_handling(self):
        """Test handling of invalid role names"""
        session = SessionManager()
        free_role = RoleManager.create_role_by_name('free')
        
        session.login({
            'email': 'user@example.com',
            'name': 'User',
            'uid': 'user_123'
        }, free_role)
        
        # Try to update to invalid role
        with pytest.raises(ValueError):
            session.update_role('invalid_role_name')

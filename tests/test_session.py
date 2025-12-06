"""
Unit tests for Session Manager
Tests user session lifecycle, authentication state, and role management
"""

import pytest
from access_control.session import SessionManager
from access_control.roles import RoleType, Permission, GuestRole, FreeRole, AdminRole, RoleManager


@pytest.fixture
def session():
    """Create a fresh session manager for each test"""
    return SessionManager()


@pytest.fixture
def guest_user_info():
    """Sample guest user data"""
    return {
        'email': 'guest@example.com',
        'name': 'Guest User',
        'uid': 'guest_123'
    }


@pytest.fixture
def free_user_info():
    """Sample free user data"""
    return {
        'email': 'user@example.com',
        'name': 'Test User',
        'uid': 'user_123',
        'picture': 'https://example.com/photo.jpg',
        'google_id': 'google_123'
    }


@pytest.fixture
def admin_user_info():
    """Sample admin user data"""
    return {
        'email': 'admin@example.com',
        'name': 'Admin User',
        'uid': 'admin_123',
        'picture': 'https://example.com/admin.jpg'
    }


class TestSessionManagerInitialization:
    """Test SessionManager initialization"""
    
    def test_session_starts_logged_out(self, session):
        """Test that session starts in logged out state"""
        assert session.is_logged_in is False
        assert session.current_user is None
        assert session.current_role is None
    
    def test_session_starts_not_guest(self, session):
        """Test that session doesn't start as guest"""
        assert session.is_guest is False
    
    def test_session_has_no_email_initially(self, session):
        """Test that session has no email initially"""
        assert session.email is None
    
    def test_session_has_no_uid_initially(self, session):
        """Test that session has no uid initially"""
        assert session.uid is None


class TestGuestLogin:
    """Test guest login functionality"""
    
    def test_guest_login_success(self, session, guest_user_info):
        """Test successful guest login"""
        guest_role = GuestRole()
        session.login(guest_user_info, guest_role)
        
        assert session.is_logged_in is True
        assert session.is_guest is True
        assert session.current_user == guest_user_info
        assert session.current_role.role_type == RoleType.GUEST
    
    def test_guest_not_stored_as_last_user(self, session, guest_user_info):
        """Test that guest users are not stored as last user"""
        guest_role = GuestRole()
        session.login(guest_user_info, guest_role)
        
        assert session.has_previous_user() is False
        assert session.last_user is None


class TestUserLogin:
    """Test user login functionality"""
    
    def test_free_user_login(self, session, free_user_info):
        """Test free user login"""
        free_role = FreeRole()
        session.login(free_user_info, free_role, auth_token="test_token_123")
        
        assert session.is_logged_in is True
        assert session.is_guest is False
        assert session.email == free_user_info['email']
        assert session.uid == free_user_info['uid']
        assert session.role_name == "free"
    
    def test_user_stored_as_last_user(self, session, free_user_info):
        """Test that non-guest users are stored as last user"""
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        
        assert session.has_previous_user() is True
        assert session.last_user == free_user_info
    
    def test_login_with_auth_token(self, session, free_user_info):
        """Test login with auth token"""
        free_role = FreeRole()
        auth_token = "mock_oauth_token"
        session.login(free_user_info, free_role, auth_token=auth_token)
        
        assert session.is_logged_in is True
        # Note: auth_token is private, we can only verify login succeeded


class TestAdminLogin:
    """Test admin user login"""
    
    def test_admin_login(self, session, admin_user_info):
        """Test admin user login"""
        admin_role = AdminRole()
        session.login(admin_user_info, admin_role)
        
        assert session.is_logged_in is True
        assert session.role_name == "admin"
        assert session.current_role.role_type == RoleType.ADMIN


class TestLogout:
    """Test logout functionality"""
    
    def test_logout_clears_session(self, session, free_user_info):
        """Test that logout clears session data"""
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        
        # Verify login
        assert session.is_logged_in is True
        
        # Logout
        session.logout(clear_tokens=False)  # Don't clear tokens in test
        
        # Verify logout
        assert session.is_logged_in is False
        assert session.current_user is None
        assert session.current_role is None
        assert session.email is None
        assert session.uid is None
    
    def test_logout_preserves_last_user(self, session, free_user_info):
        """Test that logout preserves last user data"""
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        session.logout(clear_tokens=False)
        
        # Last user should still be available after logout
        assert session.has_previous_user() is True
        assert session.last_user == free_user_info


class TestRoleUpdate:
    """Test role update functionality"""
    
    def test_upgrade_free_to_premium(self, session, free_user_info):
        """Test upgrading from free to premium"""
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        
        # Upgrade to premium
        success = session.update_role('premium')
        
        assert success is True
        assert session.role_name == "premium"
        assert session.current_role.role_type == RoleType.PREMIUM
    
    def test_update_role_when_not_logged_in(self, session):
        """Test that role update fails when not logged in"""
        success = session.update_role('premium')
        assert success is False
    
    def test_update_to_admin_role(self, session, free_user_info):
        """Test updating to admin role"""
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        
        success = session.update_role('admin')
        
        assert success is True
        assert session.role_name == "admin"


class TestPermissionChecking:
    """Test permission checking methods"""
    
    def test_guest_cannot_upload(self, session, guest_user_info):
        """Test that guest cannot upload videos"""
        guest_role = GuestRole()
        session.login(guest_user_info, guest_role)
        
        assert session.can_upload() is False
        assert session.has_permission("upload_video") is False
    
    def test_free_user_can_upload(self, session, free_user_info):
        """Test that free user can upload videos"""
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        
        assert session.can_upload() is True
        assert session.has_permission("upload_video") is True
    
    def test_permission_check_when_logged_out(self, session):
        """Test permission checking when not logged in"""
        assert session.has_permission("save_video") is False
        assert session.can_upload() is False
    
    def test_admin_has_manage_users_permission(self, session, admin_user_info):
        """Test that admin has user management permission"""
        admin_role = AdminRole()
        session.login(admin_user_info, admin_role)
        
        assert session.has_permission("manage_users") is True


class TestUserDisplayInfo:
    """Test user display information retrieval"""
    
    def test_get_user_display_info_when_logged_in(self, session, free_user_info):
        """Test getting user display info when logged in"""
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        
        display_info = session.get_user_display_info()
        
        assert display_info['name'] == free_user_info['name']
        assert display_info['email'] == free_user_info['email']
        assert display_info['role'] == 'free'
    
    def test_get_user_display_info_when_logged_out(self, session):
        """Test getting user display info when logged out"""
        display_info = session.get_user_display_info()
        
        assert display_info['name'] == 'Guest'
        assert display_info['email'] == 'Not logged in'
        assert display_info['role'] == 'none'


class TestUsageTracking:
    """Test usage tracking methods"""
    
    def test_increment_merge_count(self, session, free_user_info):
        """Test incrementing merge count (no errors)"""
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        
        # Should not raise error even without Firebase
        session.increment_merge_count()
    
    def test_increment_upload_count(self, session, free_user_info):
        """Test incrementing upload count (no errors)"""
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        
        # Should not raise error even without Firebase
        session.increment_upload_count()


class TestMultipleLogins:
    """Test multiple login scenarios"""
    
    def test_login_twice_updates_session(self, session, free_user_info, admin_user_info):
        """Test that logging in twice updates session properly"""
        # First login
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        assert session.email == free_user_info['email']
        
        # Second login
        admin_role = AdminRole()
        session.login(admin_user_info, admin_role)
        assert session.email == admin_user_info['email']
        assert session.role_name == "admin"
    
    def test_guest_then_user_login(self, session, guest_user_info, free_user_info):
        """Test guest login followed by regular user login"""
        # Guest login first
        guest_role = GuestRole()
        session.login(guest_user_info, guest_role)
        assert session.is_guest is True
        assert session.has_previous_user() is False
        
        # Regular user login
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        assert session.is_guest is False
        assert session.has_previous_user() is True
        assert session.last_user == free_user_info


class TestSessionProperties:
    """Test session property accessors"""
    
    def test_role_name_property(self, session, free_user_info):
        """Test role_name property"""
        assert session.role_name == "none"
        
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        assert session.role_name == "free"
    
    def test_email_property(self, session, free_user_info):
        """Test email property"""
        assert session.email is None
        
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        assert session.email == free_user_info['email']
    
    def test_uid_property(self, session, free_user_info):
        """Test uid property"""
        assert session.uid is None
        
        free_role = FreeRole()
        session.login(free_user_info, free_role)
        assert session.uid == free_user_info['uid']


class TestSessionIsolation:
    """Test that sessions are properly isolated"""
    
    def test_two_sessions_are_independent(self, free_user_info, admin_user_info):
        """Test that two session instances are independent"""
        session1 = SessionManager()
        session2 = SessionManager()
        
        # Login to session1
        free_role = FreeRole()
        session1.login(free_user_info, free_role)
        
        # Session2 should still be logged out
        assert session1.is_logged_in is True
        assert session2.is_logged_in is False
        
        # Login to session2
        admin_role = AdminRole()
        session2.login(admin_user_info, admin_role)
        
        # Both sessions should maintain their own state
        assert session1.email == free_user_info['email']
        assert session2.email == admin_user_info['email']
        assert session1.role_name == "free"
        assert session2.role_name == "admin"

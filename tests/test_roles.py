"""
Unit tests for Role Management System
Tests role creation, permissions, and RBAC functionality
"""

import pytest
from access_control.roles import (
    RoleType, Permission, Role, RoleLimits,
    GuestRole, FreeRole, PremiumRole, DevRole, AdminRole,
    RoleManager
)


class TestRoleType:
    """Test RoleType enumeration"""
    
    def test_role_type_values(self):
        """Test that all role types have correct values"""
        assert RoleType.GUEST.value == "guest"
        assert RoleType.FREE.value == "free"
        assert RoleType.PREMIUM.value == "premium"
        assert RoleType.DEV.value == "dev"
        assert RoleType.ADMIN.value == "admin"
    
    def test_role_type_count(self):
        """Test that we have exactly 5 role types"""
        assert len(RoleType) == 5


class TestPermission:
    """Test Permission enumeration"""
    
    def test_basic_permissions_exist(self):
        """Test that basic permissions are defined"""
        assert Permission.SAVE_VIDEO.value == "save_video"
        assert Permission.UPLOAD_VIDEO.value == "upload_video"
        assert Permission.MERGE_VIDEOS.value == "merge_videos"
    
    def test_feature_permissions_exist(self):
        """Test that feature permissions are defined"""
        assert Permission.NO_WATERMARK.value == "no_watermark"
        assert Permission.NO_ADS.value == "no_ads"
        assert Permission.UNLIMITED_MERGES.value == "unlimited_merges"
    
    def test_admin_permissions_exist(self):
        """Test that admin permissions are defined"""
        assert Permission.MANAGE_USERS.value == "manage_users"
        assert Permission.CHANGE_ROLES.value == "change_roles"
        assert Permission.BAN_USERS.value == "ban_users"
        assert Permission.VIEW_ANALYTICS.value == "view_analytics"


class TestRoleLimits:
    """Test RoleLimits dataclass"""
    
    def test_default_limits(self):
        """Test default limit values"""
        limits = RoleLimits()
        assert limits.max_merge_count_per_day == -1  # Unlimited
        assert limits.max_video_length_minutes == -1  # Unlimited
        assert limits.max_file_size_mb == -1  # Unlimited
        assert limits.watermark_enabled is False
        assert limits.ads_enabled is False
    
    def test_custom_limits(self):
        """Test creating custom limits"""
        limits = RoleLimits(
            max_merge_count_per_day=10,
            max_video_length_minutes=30,
            max_file_size_mb=500,
            watermark_enabled=True,
            ads_enabled=True
        )
        assert limits.max_merge_count_per_day == 10
        assert limits.max_video_length_minutes == 30
        assert limits.max_file_size_mb == 500
        assert limits.watermark_enabled is True
        assert limits.ads_enabled is True


class TestGuestRole:
    """Test Guest role"""
    
    @pytest.fixture
    def guest_role(self):
        """Create a guest role for testing"""
        return GuestRole()
    
    def test_guest_has_basic_permissions(self, guest_role):
        """Test that guest has basic permissions"""
        assert guest_role.has_permission(Permission.SAVE_VIDEO)
        assert guest_role.has_permission(Permission.MERGE_VIDEOS)
    
    def test_guest_lacks_upload_permission(self, guest_role):
        """Test that guest cannot upload videos"""
        assert not guest_role.has_permission(Permission.UPLOAD_VIDEO)
    
    def test_guest_lacks_premium_features(self, guest_role):
        """Test that guest doesn't have premium features"""
        assert not guest_role.has_permission(Permission.NO_WATERMARK)
        assert not guest_role.has_permission(Permission.NO_ADS)
    
    def test_guest_has_watermark_and_ads(self, guest_role):
        """Test that guest has watermark and ads enabled"""
        assert guest_role.limits.watermark_enabled is True
        assert guest_role.limits.ads_enabled is True
    
    def test_guest_video_length_limit(self, guest_role):
        """Test guest video length limit"""
        assert guest_role.limits.max_video_length_minutes == 10
    
    def test_guest_file_size_limit(self, guest_role):
        """Test guest file size limit"""
        assert guest_role.limits.max_file_size_mb == 100


class TestFreeRole:
    """Test Free role"""
    
    @pytest.fixture
    def free_role(self):
        """Create a free role for testing"""
        return FreeRole()
    
    def test_free_can_upload(self, free_role):
        """Test that free users can upload videos"""
        assert free_role.has_permission(Permission.UPLOAD_VIDEO)
    
    def test_free_has_basic_permissions(self, free_role):
        """Test that free has basic permissions"""
        assert free_role.has_permission(Permission.SAVE_VIDEO)
        assert free_role.has_permission(Permission.MERGE_VIDEOS)
    
    def test_free_no_watermark(self, free_role):
        """Test that free users don't have watermark"""
        assert free_role.limits.watermark_enabled is False
    
    def test_free_has_ads(self, free_role):
        """Test that free users still see ads"""
        assert free_role.limits.ads_enabled is True
    
    def test_free_video_length_limit(self, free_role):
        """Test free video length limit"""
        assert free_role.limits.max_video_length_minutes == 30


class TestPremiumRole:
    """Test Premium role"""
    
    @pytest.fixture
    def premium_role(self):
        """Create a premium role for testing"""
        return PremiumRole()
    
    def test_premium_has_all_basic_permissions(self, premium_role):
        """Test that premium has all basic permissions"""
        assert premium_role.has_permission(Permission.SAVE_VIDEO)
        assert premium_role.has_permission(Permission.UPLOAD_VIDEO)
        assert premium_role.has_permission(Permission.MERGE_VIDEOS)
    
    def test_premium_has_premium_features(self, premium_role):
        """Test that premium has premium features"""
        assert premium_role.has_permission(Permission.NO_WATERMARK)
        assert premium_role.has_permission(Permission.NO_ADS)
        assert premium_role.has_permission(Permission.UNLIMITED_MERGES)
    
    def test_premium_no_restrictions(self, premium_role):
        """Test that premium has no limits"""
        assert premium_role.limits.watermark_enabled is False
        assert premium_role.limits.ads_enabled is False
        assert premium_role.limits.max_merge_count_per_day == -1  # Unlimited
        assert premium_role.limits.max_video_length_minutes == -1  # Unlimited
        assert premium_role.limits.max_file_size_mb == -1  # Unlimited


class TestDevRole:
    """Test Developer role"""
    
    @pytest.fixture
    def dev_role(self):
        """Create a dev role for testing"""
        return DevRole()
    
    def test_dev_has_premium_permissions(self, dev_role):
        """Test that dev has all premium permissions"""
        assert dev_role.has_permission(Permission.SAVE_VIDEO)
        assert dev_role.has_permission(Permission.UPLOAD_VIDEO)
        assert dev_role.has_permission(Permission.MERGE_VIDEOS)
        assert dev_role.has_permission(Permission.NO_WATERMARK)
        assert dev_role.has_permission(Permission.NO_ADS)
        assert dev_role.has_permission(Permission.UNLIMITED_MERGES)
    
    def test_dev_has_debug_tools(self, dev_role):
        """Test that dev has access to debug tools"""
        assert dev_role.has_permission(Permission.VIEW_LOGS)
        assert dev_role.has_permission(Permission.ACCESS_DEBUG_TOOLS)
    
    def test_dev_lacks_admin_permissions(self, dev_role):
        """Test that dev doesn't have admin permissions"""
        assert not dev_role.has_permission(Permission.MANAGE_USERS)
        assert not dev_role.has_permission(Permission.CHANGE_ROLES)
        assert not dev_role.has_permission(Permission.BAN_USERS)


class TestAdminRole:
    """Test Admin role"""
    
    @pytest.fixture
    def admin_role(self):
        """Create an admin role for testing"""
        return AdminRole()
    
    def test_admin_has_all_permissions(self, admin_role):
        """Test that admin has all permissions"""
        for permission in Permission:
            assert admin_role.has_permission(permission)
    
    def test_admin_can_manage_users(self, admin_role):
        """Test that admin has user management permissions"""
        assert admin_role.has_permission(Permission.MANAGE_USERS)
        assert admin_role.has_permission(Permission.CHANGE_ROLES)
        assert admin_role.has_permission(Permission.BAN_USERS)
    
    def test_admin_has_analytics(self, admin_role):
        """Test that admin can view analytics"""
        assert admin_role.has_permission(Permission.VIEW_ANALYTICS)


class TestRoleManager:
    """Test RoleManager factory"""
    
    def test_create_guest_role(self):
        """Test creating guest role by name"""
        role = RoleManager.create_role_by_name("guest")
        assert isinstance(role, GuestRole)
        assert role.role_type == RoleType.GUEST
    
    def test_create_free_role(self):
        """Test creating free role by name"""
        role = RoleManager.create_role_by_name("free")
        assert isinstance(role, FreeRole)
        assert role.role_type == RoleType.FREE
    
    def test_create_premium_role(self):
        """Test creating premium role by name"""
        role = RoleManager.create_role_by_name("premium")
        assert isinstance(role, PremiumRole)
        assert role.role_type == RoleType.PREMIUM
    
    def test_create_dev_role(self):
        """Test creating dev role by name"""
        role = RoleManager.create_role_by_name("dev")
        assert isinstance(role, DevRole)
        assert role.role_type == RoleType.DEV
    
    def test_create_admin_role(self):
        """Test creating admin role by name"""
        role = RoleManager.create_role_by_name("admin")
        assert isinstance(role, AdminRole)
        assert role.role_type == RoleType.ADMIN
    
    def test_create_invalid_role_raises_error(self):
        """Test that invalid role name raises ValueError"""
        with pytest.raises(ValueError):
            RoleManager.create_role_by_name("invalid_role")


class TestRolePermissionChecking:
    """Test role permission checking methods"""
    
    @pytest.fixture
    def guest_role(self):
        return GuestRole()
    
    @pytest.fixture
    def admin_role(self):
        return AdminRole()
    
    def test_has_any_permission(self, guest_role):
        """Test has_any_permission method"""
        assert guest_role.has_any_permission([Permission.SAVE_VIDEO, Permission.UPLOAD_VIDEO])
        assert not guest_role.has_any_permission([Permission.UPLOAD_VIDEO, Permission.MANAGE_USERS])
    
    def test_has_all_permissions(self, guest_role, admin_role):
        """Test has_all_permissions method"""
        # Guest should not have all admin permissions
        assert not guest_role.has_all_permissions([Permission.SAVE_VIDEO, Permission.MANAGE_USERS])
        
        # Admin should have all permissions
        assert admin_role.has_all_permissions([Permission.SAVE_VIDEO, Permission.MANAGE_USERS, Permission.UPLOAD_VIDEO])
    
    def test_can_perform_action_by_string(self, guest_role):
        """Test can_perform_action method with string action names"""
        assert guest_role.can_perform_action("save_video")
        assert not guest_role.can_perform_action("manage_users")
        assert not guest_role.can_perform_action("invalid_action")


class TestRoleHierarchy:
    """Test that role hierarchy is properly enforced"""
    
    def test_guest_is_most_restrictive(self):
        """Test that guest has fewest permissions"""
        guest = GuestRole()
        free = FreeRole()
        
        # Guest should have fewer permissions than free
        guest_perms = len(guest.permissions)
        free_perms = len(free.permissions)
        assert guest_perms < free_perms
    
    def test_admin_has_most_permissions(self):
        """Test that admin has most permissions"""
        admin = AdminRole()
        dev = DevRole()
        premium = PremiumRole()
        
        admin_perms = len(admin.permissions)
        dev_perms = len(dev.permissions)
        premium_perms = len(premium.permissions)
        
        assert admin_perms > dev_perms
        assert admin_perms > premium_perms
    
    def test_premium_upgrade_path(self):
        """Test that premium has all features free users have plus more"""
        free = FreeRole()
        premium = PremiumRole()
        
        # Premium should have at least all free permissions
        for permission in free.permissions:
            assert permission in premium.permissions

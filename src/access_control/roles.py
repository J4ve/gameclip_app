"""
Role Management System - OOP Implementation
Defines all user roles and their permissions/features
"""

from dataclasses import dataclass
from typing import List, Set
from enum import Enum


class RoleType(Enum):
    """Enumeration of all available roles"""
    GUEST = "guest"
    FREE = "free"
    PREMIUM = "premium"
    DEV = "dev"
    ADMIN = "admin"


class Permission(Enum):
    """Enumeration of all permissions"""
    # Basic permissions
    SAVE_VIDEO = "save_video"
    UPLOAD_VIDEO = "upload_video"
    MERGE_VIDEOS = "merge_videos"
    
    # Feature permissions
    NO_WATERMARK = "no_watermark"
    NO_ADS = "no_ads"
    UNLIMITED_MERGES = "unlimited_merges"
    
    # Advanced permissions
    VIEW_LOGS = "view_logs"
    ACCESS_DEBUG_TOOLS = "access_debug_tools"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    CHANGE_ROLES = "change_roles"
    BAN_USERS = "ban_users"
    VIEW_ANALYTICS = "view_analytics"


@dataclass
class RoleLimits:
    """Defines limits for each role"""
    # CONFIG_MARKER: Role limits configuration
    # Set to -1 for unlimited, or positive integer for specific limits
    max_merge_count_per_day: int = -1  # -1 = unlimited
    max_video_length_minutes: int = -1  # -1 = unlimited
    max_file_size_mb: int = -1  # -1 = unlimited
    watermark_enabled: bool = False
    ads_enabled: bool = False


class Role:
    """Base role class with permissions and limitations"""
    
    def __init__(self, role_type: RoleType, permissions: Set[Permission], limits: RoleLimits, description: str = ""):
        self.role_type = role_type
        self.permissions = permissions
        self.limits = limits
        self.description = description
    
    @property
    def name(self) -> str:
        """Get role name"""
        return self.role_type.value
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if role has any of the specified permissions"""
        return any(perm in self.permissions for perm in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if role has all of the specified permissions"""
        return all(perm in self.permissions for perm in permissions)
    
    def can_perform_action(self, action: str) -> bool:
        """Check if role can perform a specific action by name"""
        try:
            permission = Permission(action)
            return self.has_permission(permission)
        except ValueError:
            return False


class GuestRole(Role):
    """Guest role - limited features with watermark and ads"""
    
    def __init__(self):
        permissions = {
            Permission.SAVE_VIDEO,
            Permission.MERGE_VIDEOS,
        }
        
        # CONFIG_MARKER: Guest user limits configuration
        # To enable daily limits, change max_merge_count_per_day from -1 to desired number (e.g., 5)
        limits = RoleLimits(
            max_merge_count_per_day=-1,  # -1 = unlimited (currently no limit)
            max_video_length_minutes=10,
            max_file_size_mb=100,
            watermark_enabled=True,
            ads_enabled=True
        )
        
        super().__init__(
            role_type=RoleType.GUEST,
            permissions=permissions,
            limits=limits,
            description="Guest user with limited features, watermark, and ads"
        )


class FreeRole(Role):
    """Free tier user - can upload but has ads"""
    
    def __init__(self):
        permissions = {
            Permission.SAVE_VIDEO,
            Permission.UPLOAD_VIDEO,
            Permission.MERGE_VIDEOS,
        }
        
        # CONFIG_MARKER: Free user limits configuration
        # To enable daily limits, change max_merge_count_per_day from -1 to desired number (e.g., 20)
        limits = RoleLimits(
            max_merge_count_per_day=-1,  # -1 = unlimited (currently no limit)
            max_video_length_minutes=30,
            max_file_size_mb=500,
            watermark_enabled=False,
            ads_enabled=True
        )
        
        super().__init__(
            role_type=RoleType.FREE,
            permissions=permissions,
            limits=limits,
            description="Free tier user with upload capability but has ads"
        )


class PremiumRole(Role):
    """Premium user - full features, no ads, no watermark"""
    
    def __init__(self):
        permissions = {
            Permission.SAVE_VIDEO,
            Permission.UPLOAD_VIDEO,
            Permission.MERGE_VIDEOS,
            Permission.NO_WATERMARK,
            Permission.NO_ADS,
            Permission.UNLIMITED_MERGES,
        }
        
        # CONFIG_MARKER: Premium user limits configuration (unlimited by design)
        limits = RoleLimits(
            max_merge_count_per_day=-1,  # Unlimited
            max_video_length_minutes=-1,  # Unlimited
            max_file_size_mb=-1,  # Unlimited
            watermark_enabled=False,
            ads_enabled=False
        )
        
        super().__init__(
            role_type=RoleType.PREMIUM,
            permissions=permissions,
            limits=limits,
            description="Premium user with full features, no ads, no watermark"
        )

class AdminRole(Role):
    """Admin role - all permissions including user management"""
    
    def __init__(self):
        permissions = {
            Permission.SAVE_VIDEO,
            Permission.UPLOAD_VIDEO,
            Permission.MERGE_VIDEOS,
            Permission.NO_WATERMARK,
            Permission.NO_ADS,
            Permission.UNLIMITED_MERGES,
            Permission.VIEW_LOGS,
            Permission.ACCESS_DEBUG_TOOLS,
            Permission.MANAGE_USERS,
            Permission.CHANGE_ROLES,
            Permission.BAN_USERS,
            Permission.VIEW_ANALYTICS,
        }
        
        # CONFIG_MARKER: Admin role limits configuration (unlimited by design)
        limits = RoleLimits(
            max_merge_count_per_day=-1,
            max_video_length_minutes=-1,
            max_file_size_mb=-1,
            watermark_enabled=False,
            ads_enabled=False
        )
        
        super().__init__(
            role_type=RoleType.ADMIN,
            permissions=permissions,
            limits=limits,
            description="Administrator with full access and user management"
        )


class RoleManager:
    """Manages role creation and validation"""
    
    _role_classes = {
        RoleType.GUEST: GuestRole,
        RoleType.FREE: FreeRole,
        RoleType.PREMIUM: PremiumRole,
        RoleType.ADMIN: AdminRole,
    }
    
    @classmethod
    def create_role(cls, role_type: RoleType) -> Role:
        """Create a role instance by type"""
        if role_type not in cls._role_classes:
            raise ValueError(f"Unknown role type: {role_type}")
        
        return cls._role_classes[role_type]()
    
    @classmethod
    def create_role_by_name(cls, role_name: str) -> Role:
        """Create a role instance by name string"""
        try:
            role_type = RoleType(role_name.lower())
            return cls.create_role(role_type)
        except ValueError:
            raise ValueError(f"Unknown role name: {role_name}")
    
    @classmethod
    def get_all_roles(cls) -> List[Role]:
        """Get instances of all available roles"""
        return [cls.create_role(role_type) for role_type in RoleType]
    
    @classmethod
    def get_role_hierarchy(cls) -> List[RoleType]:
        """Get roles ordered by privilege level (least to most)"""
        return [RoleType.GUEST, RoleType.FREE, RoleType.PREMIUM, RoleType.DEV, RoleType.ADMIN]
    
    @classmethod
    def is_role_upgrade(cls, from_role: str, to_role: str) -> bool:
        """Check if changing from one role to another is an upgrade"""
        hierarchy = cls.get_role_hierarchy()
        try:
            from_idx = hierarchy.index(RoleType(from_role.lower()))
            to_idx = hierarchy.index(RoleType(to_role.lower()))
            return to_idx > from_idx
        except (ValueError, IndexError):
            return False


# Convenience function for quick role creation
def get_role(role_name: str) -> Role:
    """Get a role instance by name (convenience function)"""
    return RoleManager.create_role_by_name(role_name)


# Export commonly used items
__all__ = [
    'Role', 'RoleType', 'Permission', 'RoleLimits',
    'GuestRole', 'FreeRole', 'PremiumRole', 'AdminRole',
    'RoleManager', 'get_role'
]
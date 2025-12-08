"""
Access Control Module
Backward compatibility imports for the access control system.
The main implementation has been moved to app.gui for better organization.
"""

# Import from the new location for backward compatibility
from access_control.session import session_manager, SessionManager
from access_control.usage_tracker import usage_tracker, UsageTracker, UsageConfig

__all__ = [
    'Role', 'RoleType', 'Permission', 'RoleLimits',
    'GuestRole', 'FreeRole', 'PremiumRole', 'AdminRole', 
    'RoleManager', 'get_role',
    'SessionManager', 'session_manager',
    'UsageTracker', 'usage_tracker', 'UsageConfig'
]
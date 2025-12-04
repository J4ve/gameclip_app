"""
Access Control Module
Backward compatibility imports for the access control system.
The main implementation has been moved to app.gui for better organization.
"""

# Import from the new location for backward compatibility
from access_control.session import session_manager, SessionManager

__all__ = [
    'Role', 'RoleType', 'Permission', 'RoleLimits',
    'GuestRole', 'NormalRole', 'PremiumRole', 'DevRole', 'AdminRole', 
    'RoleManager', 'get_role',
    'SessionManager', 'session_manager'
]
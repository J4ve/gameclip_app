"""
User Session Manager
Handles user authentication state and role management throughout the app
"""

from typing import Optional, Dict, Any
from access_control.roles import Role, RoleManager, RoleType


class SessionManager:
    """Manages user session and role state throughout the app"""
    
    def __init__(self):
        self._current_user: Optional[Dict[str, Any]] = None
        self._current_role: Optional[Role] = None
        self._is_logged_in: bool = False
        self._auth_token: Optional[str] = None
        self._last_user: Optional[Dict[str, Any]] = None  # Store last logged in user
    
    @property
    def current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user info"""
        return self._current_user
    
    @property
    def current_role(self) -> Optional[Role]:
        """Get current user role"""
        return self._current_role
    
    @property
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return self._is_logged_in
    
    @property
    def is_guest(self) -> bool:
        """Check if user is a guest"""
        return self._current_role and self._current_role.role_type == RoleType.GUEST
    
    @property
    def email(self) -> Optional[str]:
        """Get current user email"""
        return self._current_user.get('email') if self._current_user else None
    
    @property
    def uid(self) -> Optional[str]:
        """Get current user ID"""
        return self._current_user.get('uid') if self._current_user else None
    
    @property
    def role_name(self) -> str:
        """Get current role name"""
        return self._current_role.name if self._current_role else "none"
    
    def login(self, user_info: Dict[str, Any], role: Role, auth_token: Optional[str] = None):
        """Set user session after successful login"""
        self._current_user = user_info.copy()
        self._current_role = role
        self._is_logged_in = True
        self._auth_token = auth_token
        
        # Store as last user if it's not a guest
        if role.role_type != RoleType.GUEST:
            self._last_user = user_info.copy()
        
        print(f"User logged in: {user_info.get('email', 'Unknown')} as {role.name}")
    
    def logout(self, clear_tokens: bool = True):
        """Clear user session and optionally clear OAuth tokens"""
        self._current_user = None
        self._current_role = None
        self._is_logged_in = False
        self._auth_token = None
        
        if clear_tokens:
            # Clear OAuth tokens when logging out
            self._clear_oauth_tokens()
        
        print("User logged out")
    
    def _clear_oauth_tokens(self):
        """Clear OAuth token files"""
        import os
        token_files = [
            "uploader/token.pickle",
            "uploader/token.json", 
            "token.pickle",
            "token.json"
        ]
        
        for token_file in token_files:
            try:
                if os.path.exists(token_file):
                    os.remove(token_file)
                    print(f"Cleared OAuth token: {token_file}")
            except Exception as e:
                print(f"Could not clear token {token_file}: {e}")
    
    @property
    def last_user(self) -> Optional[Dict[str, Any]]:
        """Get last logged in user (non-guest)"""
        return self._last_user
    
    def has_previous_user(self) -> bool:
        """Check if there's a previous non-guest user"""
        return self._last_user is not None
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if current user has specific permission"""
        if not self._current_role:
            return False
        
        return self._current_role.can_perform_action(permission_name)
    
    def can_upload(self) -> bool:
        """Check if user can upload videos"""
        return self.has_permission("upload_video")
    
    def can_save(self) -> bool:
        """Check if user can save videos"""
        return self.has_permission("save_video")
    
    def can_merge(self) -> bool:
        """Check if user can merge videos"""
        return self.has_permission("merge_videos")
    
    def has_ads(self) -> bool:
        """Check if user should see ads"""
        if not self._current_role:
            return True
        return self._current_role.limits.ads_enabled
    
    def has_watermark(self) -> bool:
        """Check if videos should have watermark"""
        if not self._current_role:
            return True
        return self._current_role.limits.watermark_enabled
    
    def get_merge_limit(self) -> int:
        """Get daily merge limit (-1 = unlimited)"""
        if not self._current_role:
            return 0
        return self._current_role.limits.max_merge_count_per_day
    
    def get_video_length_limit(self) -> int:
        """Get video length limit in minutes (-1 = unlimited)"""
        if not self._current_role:
            return 0
        return self._current_role.limits.max_video_length_minutes
    
    def get_file_size_limit(self) -> int:
        """Get file size limit in MB (-1 = unlimited)"""
        if not self._current_role:
            return 0
        return self._current_role.limits.max_file_size_mb
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self._current_role and self._current_role.role_type == RoleType.ADMIN
    
    def is_dev(self) -> bool:
        """Check if user is developer"""
        return self._current_role and self._current_role.role_type == RoleType.DEV
    
    def is_premium(self) -> bool:
        """Check if user is premium"""
        return self._current_role and self._current_role.role_type == RoleType.PREMIUM
    
    def is_normal(self) -> bool:
        """Check if user is normal/standard user"""
        return self._current_role and self._current_role.role_type == RoleType.NORMAL
    
    def get_user_display_info(self) -> Dict[str, str]:
        """Get formatted user info for display"""
        if not self._current_user or not self._current_role:
            return {
                'email': 'Not logged in',
                'role': 'None',
                'status': 'Offline'
            }
        
        status = "Guest" if self.is_guest else "Logged in"
        
        return {
            'email': self._current_user.get('email', 'Unknown'),
            'name': self._current_user.get('name', None),  # Add name field
            'role': self._current_role.name.title(),
            'status': status,
            'permissions': f"{len(self._current_role.permissions)} permissions"
        }


# Global session manager instance
session_manager = SessionManager()

# Export the instance and class
__all__ = ['SessionManager', 'session_manager']
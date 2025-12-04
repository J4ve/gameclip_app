"""
User Session Manager with Firebase Integration
Handles user authentication state, role management, and Firebase sync throughout the app
"""

from typing import Optional, Dict, Any
from access_control.roles import Role, RoleManager, RoleType


class SessionManager:
    """Manages user session and role state throughout the app with Firebase integration"""
    
    def __init__(self):
        self._current_user: Optional[Dict[str, Any]] = None
        self._current_role: Optional[Role] = None
        self._is_logged_in: bool = False
        self._auth_token: Optional[str] = None
        self._last_user: Optional[Dict[str, Any]] = None  # Store last logged in user
        self._firebase_service = None  # Will be initialized when needed
    
    def _get_firebase_service(self):
        """Lazy load Firebase service to avoid import issues"""
        if self._firebase_service is None:
            try:
                from access_control.firebase_service import get_firebase_service
                self._firebase_service = get_firebase_service()
            except ImportError as e:
                print(f"Firebase service not available: {e}")
                self._firebase_service = None
        return self._firebase_service
    
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
        """Set user session after successful login and sync with Firebase"""
        self._current_user = user_info.copy()
        self._current_role = role
        self._is_logged_in = True
        self._auth_token = auth_token
        
        # Store as last user if it's not a guest
        if role.role_type != RoleType.GUEST:
            self._last_user = user_info.copy()
        
        print(f"User logged in: {user_info.get('email', 'Unknown')} as {role.name}")
        
        # Sync with Firebase if available
        self._sync_user_with_firebase(user_info, role)
    
    def _sync_user_with_firebase(self, user_info: Dict[str, Any], role: Role):
        """Create or update user document in Firebase"""
        firebase_service = self._get_firebase_service()
        if not firebase_service or not firebase_service.is_available:
            print("Firebase not available - operating in local mode")
            return
        
        uid = user_info.get('uid')
        email = user_info.get('email')
        name = user_info.get('name')
        
        if not uid or not email:
            print("Missing UID or email - cannot sync with Firebase")
            return
        
        try:
            # Check if user exists in Firebase
            existing_user = firebase_service.get_user_data(uid)
            
            if existing_user:
                # User exists - update last login
                firebase_service.update_last_login(uid)
                
                # Check if role needs updating
                firebase_role = existing_user.get('role', 'normal')
                if firebase_role != role.name:
                    print(f"Role mismatch: local={role.name}, firebase={firebase_role}")
                    # Update local role to match Firebase (Firebase is source of truth)
                    try:
                        self._current_role = RoleManager.create_role_by_name(firebase_role)
                        print(f"Updated local role to match Firebase: {firebase_role}")
                    except ValueError:
                        print(f"Invalid Firebase role: {firebase_role}, keeping local role: {role.name}")
                        firebase_service.update_user_role(uid, role.name)
            else:
                # New user - create document
                firebase_service.create_user_document(uid, email, name, role.name)
                
        except Exception as e:
            print(f"Error syncing with Firebase: {e}")
    
    def update_role(self, new_role: str) -> bool:
        """Update user role (for purchases, upgrades, etc.)"""
        if not self._current_user or not self._is_logged_in:
            return False
        
        firebase_service = self._get_firebase_service()
        uid = self._current_user.get('uid')
        
        try:
            # Update local role
            new_role_obj = RoleManager.create_role_by_name(new_role)
            self._current_role = new_role_obj
            
            # Update Firebase if available
            if firebase_service and firebase_service.is_available and uid:
                firebase_service.update_user_role(uid, new_role)
            
            print(f"User role updated to: {new_role}")
            return True
            
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False
    
    def increment_merge_count(self):
        """Increment merge count in Firebase"""
        firebase_service = self._get_firebase_service()
        uid = self.uid
        
        if firebase_service and firebase_service.is_available and uid:
            firebase_service.increment_merge_count(uid)
    
    def increment_upload_count(self):
        """Increment upload count in Firebase"""
        firebase_service = self._get_firebase_service()
        uid = self.uid
        
        if firebase_service and firebase_service.is_available and uid:
            firebase_service.increment_upload_count(uid)
    
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
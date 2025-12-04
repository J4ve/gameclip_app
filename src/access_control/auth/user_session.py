"""
User session manager for Video Merger App
Handles current user state, role checking, and token management
"""

from typing import Optional, Dict, Any
import pickle
import os

class UserSession:
    """
    Manages the current user session (logged in user, role, token).
    Persists across app restarts using pickle.
    """
    
    def __init__(self):
        self._user: Optional[Dict[str, Any]] = None
        self._token: Optional[str] = None
        self._session_file = os.path.join(os.path.dirname(__file__), '.user_session')
        self._load_session()
    
    def _load_session(self):
        """Load saved session from disk if available."""
        if os.path.exists(self._session_file):
            try:
                with open(self._session_file, 'rb') as f:
                    data = pickle.load(f)
                    self._user = data.get('user')
                    self._token = data.get('token')
                    print(f"✓ Loaded session for {self._user.get('email') if self._user else 'guest'}")
            except Exception as e:
                print(f"Failed to load session: {e}")
    
    def _save_session(self):
        """Save current session to disk."""
        try:
            with open(self._session_file, 'wb') as f:
                pickle.dump({'user': self._user, 'token': self._token}, f)
        except Exception as e:
            print(f"Failed to save session: {e}")
    
    def login(self, user: Dict[str, Any], token: str):
        """Set the current user and token."""
        self._user = user
        self._token = token
        self._save_session()
        print(f"✓ Logged in as {user.get('email')} (role: {user.get('role')})")
    
    def logout(self):
        """Clear the current user session."""
        self._user = None
        self._token = None
        if os.path.exists(self._session_file):
            os.remove(self._session_file)
        print("✓ Logged out")
    
    @property
    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        return self._user is not None
    
    @property
    def user(self) -> Optional[Dict[str, Any]]:
        """Get current user info."""
        return self._user
    
    @property
    def token(self) -> Optional[str]:
        """Get current Firebase ID token."""
        return self._token
    
    @property
    def role(self) -> str:
        """Get current user role (guest if not logged in)."""
        if not self._user:
            return 'guest'
        return self._user.get('role', 'guest')
    
    @property
    def uid(self) -> Optional[str]:
        """Get current user UID."""
        if not self._user:
            return None
        return self._user.get('uid')
    
    @property
    def email(self) -> Optional[str]:
        """Get current user email."""
        if not self._user:
            return None
        return self._user.get('email')
    
    def has_role(self, *roles) -> bool:
        """Check if user has one of the specified roles."""
        return self.role in roles
    
    def is_premium(self) -> bool:
        """Check if user is premium (no ads)."""
        return self.role in ['premium', 'dev', 'admin']
    
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == 'admin'
    
    def is_dev(self) -> bool:
        """Check if user is dev or admin."""
        return self.role in ['dev', 'admin']


# Singleton instance
user_session = UserSession()

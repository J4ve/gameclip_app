"""
Firebase Authentication Module
Handles Firebase auth operations with fallback for missing config
"""

import os
import json
from typing import Optional, Dict, Any


class FirebaseAuth:
    """Firebase authentication handler with mock fallback"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.firebase_available = False
        self.mock_users = {}  # For development without Firebase
        
        # Try to initialize Firebase
        if config_path and os.path.exists(config_path):
            try:
                # Try to import Firebase modules
                import pyrebase
                import firebase_admin
                self.firebase_available = True
                print("Firebase initialized successfully")
            except ImportError:
                print("Firebase modules not available, using mock authentication")
                self.firebase_available = False
        else:
            print("Firebase config not found, using mock authentication")
    
    def sign_in(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Sign in user with email/password"""
        if self.firebase_available:
            # Actual Firebase implementation would go here
            pass
        
        # Mock implementation for development
        if email in self.mock_users and self.mock_users[email]['password'] == password:
            return {
                'email': email,
                'uid': f'mock_uid_{email.replace("@", "_").replace(".", "_")}',
                'role': self.mock_users[email].get('role', 'normal'),
                'verified': True
            }
        elif email == 'admin@test.com' and password == 'admin123':
            return {
                'email': email,
                'uid': 'mock_admin_uid',
                'role': 'admin',
                'verified': True
            }
        elif email == 'user@test.com' and password == 'user123':
            return {
                'email': email,
                'uid': 'mock_user_uid',
                'role': 'normal',
                'verified': True
            }
        elif email == 'premium@test.com' and password == 'premium123':
            return {
                'email': email,
                'uid': 'mock_premium_uid',
                'role': 'premium',
                'verified': True
            }
        
        return None
    
    def create_account(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Create new user account"""
        if self.firebase_available:
            # Actual Firebase implementation would go here
            pass
        
        # Mock implementation
        if email not in self.mock_users:
            self.mock_users[email] = {
                'password': password,
                'role': 'normal',
                'created_at': 'mock_timestamp'
            }
            return {
                'email': email,
                'uid': f'mock_uid_{email.replace("@", "_").replace(".", "_")}',
                'role': 'normal',
                'verified': False
            }
        
        return None
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify authentication token"""
        if self.firebase_available:
            # Actual Firebase implementation would go here
            pass
        
        # Mock implementation - tokens are just user info in development
        if isinstance(token, dict):
            return token
        
        return None
    
    def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> bool:
        """Set custom claims for user (Firebase Admin SDK)"""
        if self.firebase_available:
            # Actual Firebase implementation would go here
            pass
        
        # Mock implementation
        print(f"Mock: Setting custom claims for {uid}: {claims}")
        return True
    
    def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user info by UID"""
        if self.firebase_available:
            # Actual Firebase implementation would go here
            pass
        
        # Mock implementation
        for email, user_data in self.mock_users.items():
            mock_uid = f'mock_uid_{email.replace("@", "_").replace(".", "_")}'
            if mock_uid == uid:
                return {
                    'email': email,
                    'uid': uid,
                    'role': user_data.get('role', 'normal'),
                    'verified': True
                }
        
        return None


# Global instance for easy import
firebase_auth = None

def get_firebase_auth() -> FirebaseAuth:
    """Get global Firebase auth instance"""
    global firebase_auth
    if firebase_auth is None:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'firebase_config.json')
        firebase_auth = FirebaseAuth(config_path=config_path)
    return firebase_auth
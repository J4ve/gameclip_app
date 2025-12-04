"""
Firebase Authentication Module for Video Merger App
Handles user authentication, role management, and custom claims using Firebase Admin SDK
"""

import os
import json
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, auth

class FirebaseAuth:
    """
    Firebase authentication and role management for the Video Merger App.
    
    Roles: guest, normal, premium, dev, admin
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True
    
    def _initialize_firebase(self):
        """
        Initialize Firebase Admin SDK.
        
        Set FIREBASE_SERVICE_ACCOUNT env var to path of service account JSON,
        or place serviceAccountKey.json in this directory.
        """
        if firebase_admin._apps:
            return  # Already initialized
        
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT', 
                                         os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json'))
        
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print(f"✓ Firebase Admin initialized with {service_account_path}")
        else:
            print(f"⚠ Firebase service account not found at {service_account_path}")
            print("  Set FIREBASE_SERVICE_ACCOUNT env var or place serviceAccountKey.json in access_control/auth/")
    
    def verify_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a Firebase ID token and return decoded claims.
        
        Returns: dict with uid, email, role (from custom claims), or None if invalid
        """
        try:
            decoded = auth.verify_id_token(id_token)
            return {
                'uid': decoded.get('uid'),
                'email': decoded.get('email'),
                'role': decoded.get('role', 'guest'),  # Default to guest if no role set
                'claims': decoded
            }
        except Exception as e:
            print(f"Token verification failed: {e}")
            return None
    
    def set_user_role(self, uid: str, role: str) -> bool:
        """
        Set custom claim (role) for a user. Admin only.
        
        Valid roles: guest, normal, premium, dev, admin
        
        Returns: True if successful
        """
        valid_roles = ['guest', 'normal', 'premium', 'dev', 'admin']
        if role not in valid_roles:
            print(f"Invalid role: {role}. Must be one of {valid_roles}")
            return False
        
        try:
            auth.set_custom_user_claims(uid, {'role': role})
            print(f"✓ Set role '{role}' for user {uid}")
            return True
        except Exception as e:
            print(f"Failed to set role: {e}")
            return False
    
    def get_user_role(self, uid: str) -> str:
        """
        Get the role of a user by UID.
        
        Returns: role string or 'guest' if not found
        """
        try:
            user = auth.get_user(uid)
            claims = user.custom_claims or {}
            return claims.get('role', 'guest')
        except Exception as e:
            print(f"Failed to get user role: {e}")
            return 'guest'
    
    def list_users(self, max_results: int = 1000) -> list:
        """
        List all users (admin only).
        
        Returns: list of dicts with uid, email, role
        """
        try:
            users = []
            page = auth.list_users(max_results=max_results)
            for user in page.users:
                claims = user.custom_claims or {}
                users.append({
                    'uid': user.uid,
                    'email': user.email,
                    'displayName': user.display_name,
                    'role': claims.get('role', 'guest')
                })
            return users
        except Exception as e:
            print(f"Failed to list users: {e}")
            return []
    
    def delete_user(self, uid: str) -> bool:
        """
        Delete a user (admin only).
        
        Returns: True if successful
        """
        try:
            auth.delete_user(uid)
            print(f"✓ Deleted user {uid}")
            return True
        except Exception as e:
            print(f"Failed to delete user: {e}")
            return False


# Singleton instance
firebase_auth = FirebaseAuth()

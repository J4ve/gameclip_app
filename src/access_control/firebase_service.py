"""
Firebase Admin SDK Service
Handles user management, role assignments, and Firestore operations
"""

import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class FirebaseService:
    """Firebase Admin SDK service for user and role management"""
    
    def __init__(self, service_account_path: str = None):
        """Initialize Firebase Admin SDK with service account key"""
        if service_account_path is None:
            # Default path - place your firebase-admin-key.json in the existing configs folder
            service_account_path = os.path.join(
                os.path.dirname(__file__), 
                "..", "..", "configs", "firebase-admin-key.json"
            )
        
        self.service_account_path = service_account_path
        self._db = None
        self._initialized = False
        
        # Try to initialize Firebase
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not os.path.exists(self.service_account_path):
                print(f"Firebase service account key not found at: {self.service_account_path}")
                print("Place your firebase-admin-key.json file in the configs/ folder")
                return False
            
            # Check if Firebase is already initialized
            try:
                firebase_admin.get_app()
                print("Firebase already initialized")
                self._initialized = True
            except ValueError:
                # Initialize Firebase
                cred = credentials.Certificate(self.service_account_path)
                firebase_admin.initialize_app(cred)
                print("Firebase Admin SDK initialized successfully")
                self._initialized = True
            
            # Initialize Firestore
            if self._initialized:
                self._db = firestore.client()
                print("Firestore client initialized")
                return True
                
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")
            self._initialized = False
            return False
        
        return False
    
    @property
    def db(self):
        """Get Firestore database client"""
        if not self._initialized:
            self._initialize_firebase()
        return self._db
    
    @property
    def is_available(self) -> bool:
        """Check if Firebase is properly initialized"""
        return self._initialized and self._db is not None
    
    # User Management Methods
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user document in Firestore"""
        if not self.is_available:
            raise Exception("Firebase not available")
        
        try:
            # Prepare user document
            user_doc = {
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'role': user_data.get('role', 'normal'),
                'provider': user_data.get('provider', 'google'),
                'created_at': datetime.now(timezone.utc),
                'last_login': datetime.now(timezone.utc),
                'usage_count': 0,
                'daily_usage': 0,
                'daily_reset_date': datetime.now(timezone.utc).date().isoformat(),
                'premium_until': user_data.get('premium_until'),
                'google_id': user_data.get('google_id'),
                'uid': user_data.get('uid'),
                'picture': user_data.get('picture'),
                'authenticated': user_data.get('authenticated', True)
            }
            
            # Use email as document ID for easy lookup
            doc_id = user_data.get('email', user_data.get('uid', 'unknown'))
            
            # Create document
            doc_ref = self.db.collection('users').document(doc_id)
            doc_ref.set(user_doc)
            
            print(f"Created user document for {user_doc['email']}")
            return user_doc
            
        except Exception as e:
            print(f"Failed to create user: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user document by email"""
        if not self.is_available:
            return None
        
        try:
            doc_ref = self.db.collection('users').document(email)
            doc = doc_ref.get()
            
            if doc.exists:
                user_data = doc.to_dict()
                print(f"Retrieved user: {email}")
                return user_data
            else:
                print(f"User not found: {email}")
                return None
                
        except Exception as e:
            print(f"Failed to get user by email: {e}")
            return None
    
    def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user document by UID"""
        if not self.is_available:
            return None
        
        try:
            # Query by UID field
            users_ref = self.db.collection('users')
            query = users_ref.where('uid', '==', uid).limit(1)
            docs = query.stream()
            
            for doc in docs:
                user_data = doc.to_dict()
                print(f"Retrieved user by UID: {uid}")
                return user_data
                
            print(f"User not found by UID: {uid}")
            return None
            
        except Exception as e:
            print(f"Failed to get user by UID: {e}")
            return None
    
    def update_user_role(self, email: str, new_role: str) -> bool:
        """Update user's role"""
        if not self.is_available:
            return False
        
        try:
            doc_ref = self.db.collection('users').document(email)
            doc_ref.update({
                'role': new_role,
                'updated_at': datetime.now(timezone.utc)
            })
            
            print(f"Updated role for {email} to {new_role}")
            return True
            
        except Exception as e:
            print(f"Failed to update user role: {e}")
            return False
    
    def update_user_last_login(self, uid_or_email: str) -> bool:
        """Update user's last login timestamp by UID or email"""
        if not self.is_available:
            return False
        
        try:
            # Try to find by email first (email is the document ID)
            doc_ref = self.db.collection('users').document(uid_or_email)
            doc = doc_ref.get()
            
            if doc.exists:
                doc_ref.update({
                    'last_login': datetime.now(timezone.utc)
                })
                print(f"Updated last login for {uid_or_email}")
                return True
            else:
                # Try to find by UID if email document doesn't exist
                users_ref = self.db.collection('users')
                query = users_ref.where('uid', '==', uid_or_email).limit(1)
                docs = list(query.stream())
                
                if docs:
                    docs[0].reference.update({
                        'last_login': datetime.now(datetime.utc)
                    })
                    print(f"Updated last login for UID {uid_or_email}")
                    return True
                else:
                    print(f"User not found: {uid_or_email}")
                    return False
            
        except Exception as e:
            print(f"Failed to update last login: {e}")
            return False
    
    def increment_usage_count(self, email: str) -> bool:
        """Increment user's usage count"""
        if not self.is_available:
            return False
        
        try:
            doc_ref = self.db.collection('users').document(email)
            doc_ref.update({
                    'usage_count': firestore.Increment(1),
                    'updated_at': datetime.now(timezone.utc)
            })
            
            print(f"Incremented usage count for {email}")
            return True
            
        except Exception as e:
            print(f"Failed to increment usage count: {e}")
            return False
    
    def increment_daily_usage(self, email: str) -> bool:
        """Increment user's daily usage count, reset if new day"""
        if not self.is_available:
            return False
        
        try:
            doc_ref = self.db.collection('users').document(email)
            doc = doc_ref.get()
            
            if doc.exists:
                user_data = doc.to_dict()
                today = datetime.now(datetime.utc).date().isoformat()
                
                # Reset daily count if new day
                if user_data.get('daily_reset_date') != today:
                    doc_ref.update({
                        'daily_usage': 1,
                        'daily_reset_date': today,
                        'updated_at': datetime.now(timezone.utc)
                    })
                    print(f"Reset daily usage for {email} (new day)")
                else:
                    doc_ref.update({
                        'daily_usage': firestore.Increment(1),
                        'updated_at': datetime.now(timezone.utc)
                    })
                    print(f"Incremented daily usage for {email}")
                
                return True
            
        except Exception as e:
            print(f"Failed to increment daily usage: {e}")
            return False
    
    def set_premium_until(self, email: str, premium_until: datetime) -> bool:
        """Set user's premium expiration date"""
        if not self.is_available:
            return False
        
        try:
            doc_ref = self.db.collection('users').document(email)
            doc_ref.update({
                'premium_until': premium_until,
                'role': 'premium' if premium_until > datetime.now(timezone.utc) else 'normal',
                'updated_at': datetime.now(timezone.utc)
            })
            
            print(f"Set premium until {premium_until} for {email}")
            return True
            
        except Exception as e:
            print(f"Failed to set premium until: {e}")
            return False
    
    def check_premium_status(self, email: str) -> bool:
        """Check if user has active premium subscription"""
        if not self.is_available:
            return False
        
        try:
            user_data = self.get_user_by_email(email)
            if user_data and user_data.get('premium_until'):
                premium_until = user_data['premium_until']
                
                # Handle both datetime objects and strings
                if isinstance(premium_until, str):
                    from datetime import datetime as dt
                    premium_until = dt.fromisoformat(premium_until.replace('Z', '+00:00'))
                
                is_premium = premium_until > datetime.now(timezone.utc)
                
                # Update role if premium expired
                if not is_premium and user_data.get('role') == 'premium':
                    self.update_user_role(email, 'normal')
                
                return is_premium
            
            return False
            
        except Exception as e:
            print(f"Failed to check premium status: {e}")
            return False
    
    def get_all_users(self) -> list:
        """Get all users (admin function)"""
        if not self.is_available:
            return []
        
        try:
            users_ref = self.db.collection('users')
            docs = users_ref.stream()
            
            users = []
            for doc in docs:
                user_data = doc.to_dict()
                user_data['doc_id'] = doc.id
                users.append(user_data)
            
            print(f"Retrieved {len(users)} users")
            return users
            
        except Exception as e:
            print(f"Failed to get all users: {e}")
            return []


# Global Firebase service instance
_firebase_service_instance = None

def get_firebase_service() -> Optional[FirebaseService]:
    """Get the global Firebase service instance"""
    global _firebase_service_instance
    
    if _firebase_service_instance is None:
        try:
            _firebase_service_instance = FirebaseService()
        except Exception as e:
            print(f"Failed to create Firebase service: {e}")
            return None
    
    return _firebase_service_instance if _firebase_service_instance.is_available else None
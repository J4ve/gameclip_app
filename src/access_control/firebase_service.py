"""
Firebase Admin SDK Service
Handles user management, role assignments, and Firestore operations
"""

import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.path_helper import get_resource_path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class FirebaseService:
    """Firebase Admin SDK service for user and role management"""
    
    def __init__(self, service_account_path: str = None):
        """Initialize Firebase Admin SDK with service account key"""
        if service_account_path is None:
            # Default path - place your firebase-admin-key.json in the existing configs folder
            service_account_path = get_resource_path(os.path.join("configs", "firebase-admin-key.json"))
        
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
                'role': user_data.get('role', 'free'),
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
    
    def create_user_placeholder(self, email: str, role: str) -> bool:
        """
        Create a placeholder user document for a user who hasn't logged in yet
        This allows admins to pre-assign roles before first login
        
        Args:
            email: User's email address
            role: Role to assign (free, premium, admin)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            # Check if user already exists
            existing = self.get_user_by_email(email)
            if existing:
                # User exists, just update role
                return self.update_user_role(email, role)
            
            # Create placeholder document
            user_doc = {
                'email': email,
                'name': 'Pending',
                'role': role,
                'provider': 'placeholder',
                'created_at': datetime.now(timezone.utc),
                'last_login': None,
                'usage_count': 0,
                'daily_usage': 0,
                'daily_reset_date': datetime.now(timezone.utc).date().isoformat(),
                'premium_until': None,
                'google_id': None,
                'uid': None,
                'picture': None,
                'authenticated': False,
                'placeholder': True  # Mark as placeholder
            }
            
            # Use email as document ID
            doc_ref = self.db.collection('users').document(email)
            doc_ref.set(user_doc)
            
            print(f"Created placeholder user document for {email} with role {role}")
            return True
            
        except Exception as e:
            print(f"Failed to create placeholder user: {e}")
            return False
    
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
                        'last_login': datetime.now(timezone.utc)
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
                today = datetime.now(timezone.utc).date().isoformat()
                
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
                'role': 'premium' if premium_until > datetime.now(timezone.utc) else 'free',
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
                    self.update_user_role(email, 'free')
                
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
    
    # Security & Admin Methods
    
    def verify_admin_permission(self, uid_or_email: str) -> bool:
        """
        Verify user has admin role in Firestore (backend verification)
        
        TODO: Add additional checks:
        - Session token validation
        - Rate limiting
        - IP whitelist verification
        
        Args:
            uid_or_email: User ID or email to verify
            
        Returns:
            bool: True if user is admin, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            # Try to get user by email first, then by UID
            user = self.get_user_by_email(uid_or_email)
            if not user:
                user = self.get_user_by_uid(uid_or_email)
            
            if not user:
                print(f"[SECURITY] User not found for verification: {uid_or_email}")
                return False
            
            role = user.get('role', '').lower()
            is_admin = role == 'admin'
            
            print(f"[SECURITY] Admin verification for {uid_or_email}: {is_admin} (role: {role})")
            return is_admin
            
        except Exception as e:
            print(f"[SECURITY] Admin verification error: {e}")
            return False
    
    def disable_user(self, email: str) -> bool:
        """
        Disable user account (soft delete)
        
        TODO: Implement full functionality:
        - Set 'disabled' field to True
        - Revoke active sessions
        - Log to audit trail
        
        Args:
            email: User email to disable
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            doc_ref = self.db.collection('users').document(email)
            doc_ref.update({
                'disabled': True,
                'disabled_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            })
            
            print(f"[ADMIN] Disabled user: {email}")
            # TODO: Log to audit trail
            return True
            
        except Exception as e:
            print(f"Failed to disable user: {e}")
            return False
    
    def enable_user(self, email: str) -> bool:
        """
        Enable previously disabled user account
        
        Args:
            email: User email to enable
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            doc_ref = self.db.collection('users').document(email)
            doc_ref.update({
                'disabled': False,
                'enabled_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            })
            
            print(f"[ADMIN] Enabled user: {email}")
            # TODO: Log to audit trail
            return True
            
        except Exception as e:
            print(f"Failed to enable user: {e}")
            return False
    
    def delete_user(self, email: str) -> bool:
        """
        Permanently delete user account
        
        TODO: Implement full functionality:
        - Archive user data before deletion
        - Delete from Firebase Auth
        - Log to audit trail
        - Handle cascade deletion of related data
        
        Args:
            email: User email to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            # TODO: Archive user data first
            # TODO: Delete from Firebase Auth
            
            doc_ref = self.db.collection('users').document(email)
            doc_ref.delete()
            
            print(f"[ADMIN] Deleted user: {email}")
            # TODO: Log to audit trail
            return True
            
        except Exception as e:
            print(f"Failed to delete user: {e}")
            return False
    
    def log_admin_action(self, admin_email: str, action: str, target_user: str, 
                        details: Optional[Dict[str, Any]] = None, success: bool = True) -> bool:
        """
        Log administrative action to Firestore audit trail
        
        Creates a permanent audit record in the 'admin_audit_logs' collection.
        Each log entry includes:
        - Admin who performed the action
        - Action type (role_change, user_creation, user_deletion, etc.)
        - Target user affected
        - Timestamp (UTC)
        - Success/failure status
        - Additional details (old/new values, reasons, etc.)
        - Session information for traceability
        
        NOTE: IP address capture requires client-side context that isn't available
        in desktop apps. For production web apps, implement IP capture via request headers.
        
        Args:
            admin_email: Email of admin performing action
            action: Action type (role_change, user_creation, user_deletion, user_update)
            target_user: Email of user being affected
            details: Additional details about the action (dict)
            success: Whether action succeeded
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        if not self.is_available:
            print("[AUDIT] Skipped logging - Firebase unavailable")
            return False
        
        try:
            # Import session_manager to get session ID
            from access_control.session import session_manager
            
            # Create audit log entry
            log_entry = {
                'admin_email': admin_email,
                'action': action,
                'target_user': target_user,
                'details': details or {},
                'success': success,
                'timestamp': datetime.now(timezone.utc),
                'session_id': session_manager.session_id if hasattr(session_manager, 'session_id') else 'unknown',
                'client_type': 'desktop_app',  # Identifies this as desktop client
                # Note: IP address not available in desktop apps without external service
                # For web apps, capture via request.remote_addr or X-Forwarded-For header
            }
            
            # Store in Firestore 'admin_audit_logs' collection
            doc_ref = self.db.collection('admin_audit_logs').document()
            doc_ref.set(log_entry)
            
            # Console log for development/debugging
            status_emoji = "✅" if success else "❌"
            print(f"[AUDIT] {status_emoji} {admin_email} -> {action} on {target_user}")
            print(f"        Details: {details}")
            
            return True
            
        except Exception as e:
            print(f"[AUDIT ERROR] Failed to log action: {e}")
            # Don't fail the operation if logging fails, just warn
            return False
    
    def get_audit_logs(self, limit: int = 100, admin_filter: str = None, 
                       action_filter: str = None, target_user_filter: str = None,
                       start_date: datetime = None, end_date: datetime = None) -> list:
        """
        Retrieve audit logs from Firestore for admin review
        
        Args:
            limit: Maximum number of logs to return (default 100)
            admin_filter: Filter by admin email (actor who performed the action)
            action_filter: Filter by action type (role_change, user_creation, etc.)
            target_user_filter: Filter by target user email (user who was affected)
            start_date: Only return logs after this date (optional)
            end_date: Only return logs before this date (optional)
            
        Returns:
            list: List of audit log dictionaries, newest first
        """
        if not self.is_available:
            return []
        
        try:
            # Start with base query
            query = self.db.collection('admin_audit_logs').order_by(
                'timestamp', direction=firestore.Query.DESCENDING
            )
            
            # Apply filters
            # Note: Firestore has limitations on multiple inequality filters
            # If using multiple date filters, they must be on the same field
            
            # CLIENT-SIDE FILTERING ADAPTATION:
            # We only apply date filters in the query to avoid composite index requirements
            # (e.g. admin_email + timestamp) which cause 400 errors without manual indexing.
            
            if start_date:
                query = query.where('timestamp', '>=', start_date)
            
            if end_date:
                query = query.where('timestamp', '<=', end_date)
            
            # Execute query with limit
            docs = query.limit(limit).stream()
            
            logs = []
            for doc in docs:
                log_data = doc.to_dict()
                
                # Apply client-side filters
                if admin_filter and log_data.get('admin_email') != admin_filter:
                    continue
                
                if action_filter and log_data.get('action') != action_filter:
                    continue
                
                if target_user_filter and log_data.get('target_user') != target_user_filter:
                    continue
                
                log_data['id'] = doc.id  # Include document ID
                logs.append(log_data)
            
            print(f"[AUDIT] Retrieved {len(logs)} audit logs")
            return logs
            
        except Exception as e:
            print(f"[AUDIT ERROR] Failed to retrieve logs: {e}")
            return []
    
    def check_rate_limit(self, user_email: str, action_type: str, max_per_minute: int = 10) -> bool:
        """
        Check if user has exceeded rate limit for action
        
        TODO: Implement full rate limiting:
        - Track action counts in memory/Redis cache
        - Different limits for different action types
        - Implement sliding window algorithm
        - Auto-block on excessive violations
        
        Args:
            user_email: Email of user performing action
            action_type: Type of action (role_change, delete, etc.)
            max_per_minute: Maximum actions allowed per minute
            
        Returns:
            bool: True if within limit, False if exceeded
        """
        # TODO: Implement actual rate limiting logic
        # For now, always return True (no limiting)
        return True
    
    # Metadata Preset Methods
    
    def create_preset(self, user_id: str, preset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a metadata preset for a user
        
        Args:
            user_id: User's email or identifier
            preset_data: Preset configuration dictionary containing:
                - name: Template name
                - title: Default title template
                - description: Default description
                - tags: Default tags
                - visibility: Default visibility
                - made_for_kids: Default made_for_kids flag
        
        Returns:
            Dict with preset data including 'id' field
        """
        if not self.is_available:
            raise Exception("Firebase not available")
        
        try:
            # Add timestamp
            preset_doc = {
                **preset_data,
                'user_id': user_id,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
            
            # Add to presets collection
            doc_ref = self.db.collection('metadata_presets').document()
            doc_ref.set(preset_doc)
            
            # Return with document ID
            preset_doc['id'] = doc_ref.id
            print(f"Created preset '{preset_data.get('name')}' for user {user_id}")
            return preset_doc
            
        except Exception as e:
            print(f"Failed to create preset: {e}")
            raise
    
    def get_user_presets(self, user_id: str) -> list:
        """
        Get all metadata presets for a user
        
        Args:
            user_id: User's email or identifier
        
        Returns:
            List of preset dictionaries
        """
        if not self.is_available:
            return []
        
        try:
            presets_ref = self.db.collection('metadata_presets')
            query = presets_ref.where('user_id', '==', user_id)
            
            # Try with ordering first (requires index)
            try:
                query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
                docs = query.stream()
            except Exception as index_error:
                # Fallback: query without ordering if index doesn't exist
                if 'index' in str(index_error).lower():
                    print(f"⚠️  Firebase index not created yet. Retrieving presets without ordering.")
                    print(f"   Create index at: https://console.firebase.google.com/project/video-merger-edc29/firestore/indexes")
                    query = presets_ref.where('user_id', '==', user_id)
                    docs = query.stream()
                else:
                    raise
            
            presets = []
            for doc in docs:
                preset_data = doc.to_dict()
                preset_data['id'] = doc.id
                presets.append(preset_data)
            
            # Sort in memory if we couldn't order in query
            if presets and 'created_at' in presets[0]:
                presets.sort(key=lambda x: x.get('created_at', datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
            
            print(f"Retrieved {len(presets)} presets for user {user_id}")
            return presets
            
        except Exception as e:
            print(f"Failed to get user presets: {e}")
            return []
    
    def update_preset(self, preset_id: str, preset_data: Dict[str, Any]) -> bool:
        """
        Update an existing metadata preset
        
        Args:
            preset_id: Document ID of the preset
            preset_data: Updated preset data
        
        Returns:
            bool: True if successful
        """
        if not self.is_available:
            return False
        
        try:
            doc_ref = self.db.collection('metadata_presets').document(preset_id)
            
            # Add updated timestamp
            update_data = {
                **preset_data,
                'updated_at': datetime.now(timezone.utc)
            }
            
            doc_ref.update(update_data)
            print(f"Updated preset {preset_id}")
            return True
            
        except Exception as e:
            print(f"Failed to update preset: {e}")
            return False
    
    def delete_preset(self, preset_id: str) -> bool:
        """
        Delete a metadata preset
        
        Args:
            preset_id: Document ID of the preset
        
        Returns:
            bool: True if successful
        """
        if not self.is_available:
            return False
        
        try:
            doc_ref = self.db.collection('metadata_presets').document(preset_id)
            doc_ref.delete()
            print(f"Deleted preset {preset_id}")
            return True
            
        except Exception as e:
            print(f"Failed to delete preset: {e}")
            return False
    
    def get_preset_by_id(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific preset by ID
        
        Args:
            preset_id: Document ID of the preset
        
        Returns:
            Preset dictionary or None
        """
        if not self.is_available:
            return None
        
        try:
            doc_ref = self.db.collection('metadata_presets').document(preset_id)
            doc = doc_ref.get()
            
            if doc.exists:
                preset_data = doc.to_dict()
                preset_data['id'] = doc.id
                return preset_data
            else:
                return None
                
        except Exception as e:
            print(f"Failed to get preset: {e}")
            return None


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
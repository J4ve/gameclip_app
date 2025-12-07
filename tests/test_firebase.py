"""
Unit tests for Firebase Service
Tests Firebase user management, role updates, and audit logging (mocked)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from access_control.firebase_service import FirebaseService


@pytest.fixture
def mock_firestore_client():
    """Mock Firestore client"""
    mock_db = Mock()
    mock_collection = Mock()
    mock_document = Mock()
    
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    
    return mock_db


@pytest.fixture
def firebase_service_unavailable():
    """Create Firebase service that's unavailable (no credentials)"""
    with patch('os.path.exists', return_value=False):
        service = FirebaseService()
    return service


@pytest.fixture
def firebase_service_available(mock_firestore_client):
    """Create Firebase service that's available (mocked)"""
    with patch('os.path.exists', return_value=True), \
         patch('firebase_admin.get_app', side_effect=ValueError()), \
         patch('firebase_admin.initialize_app'), \
         patch('firebase_admin.credentials.Certificate'), \
         patch('firebase_admin.firestore.client', return_value=mock_firestore_client):
        
        service = FirebaseService()
        service._db = mock_firestore_client
        service._initialized = True
    return service


class TestFirebaseServiceInitialization:
    """Test Firebase service initialization"""
    
    def test_service_unavailable_without_credentials(self, firebase_service_unavailable):
        """Test that service is unavailable without credentials"""
        assert firebase_service_unavailable.is_available is False
    
    def test_service_available_with_mock(self, firebase_service_available):
        """Test that service is available when properly mocked"""
        assert firebase_service_available.is_available is True
    
    def test_db_property_returns_client(self, firebase_service_available):
        """Test that db property returns Firestore client"""
        assert firebase_service_available.db is not None


class TestUserCreation:
    """Test user creation functionality"""
    
    def test_create_user_when_unavailable(self, firebase_service_unavailable):
        """Test creating user when Firebase is unavailable"""
        user_data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'role': 'free'
        }
        
        with pytest.raises(Exception, match="Firebase not available"):
            firebase_service_unavailable.create_user(user_data)
    
    def test_create_user_success(self, firebase_service_available, mock_firestore_client):
        """Test successful user creation"""
        user_data = {
            'email': 'newuser@example.com',
            'name': 'New User',
            'role': 'free',
            'uid': 'user_123'
        }
        
        # Mock document reference
        mock_doc_ref = Mock()
        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref
        
        result = firebase_service_available.create_user(user_data)
        
        assert result['email'] == user_data['email']
        assert result['role'] == 'free'
        mock_doc_ref.set.assert_called_once()
    
    def test_create_user_with_premium_data(self, firebase_service_available, mock_firestore_client):
        """Test creating user with premium subscription"""
        future_date = datetime.now(timezone.utc).replace(year=2025)
        user_data = {
            'email': 'premium@example.com',
            'name': 'Premium User',
            'role': 'premium',
            'premium_until': future_date
        }
        
        mock_doc_ref = Mock()
        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref
        
        result = firebase_service_available.create_user(user_data)
        
        assert result['role'] == 'premium'
        assert result['premium_until'] == future_date


class TestPlaceholderUserCreation:
    """Test placeholder user creation"""
    
    def test_create_placeholder_when_unavailable(self, firebase_service_unavailable):
        """Test creating placeholder when Firebase is unavailable"""
        result = firebase_service_unavailable.create_user_placeholder('test@example.com', 'premium')
        assert result is False
    
    def test_create_placeholder_new_user(self, firebase_service_available, mock_firestore_client):
        """Test creating placeholder for new user"""
        # Mock get_user_by_email to return None (user doesn't exist)
        firebase_service_available.get_user_by_email = Mock(return_value=None)
        
        mock_doc_ref = Mock()
        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref
        
        result = firebase_service_available.create_user_placeholder('newuser@example.com', 'premium')
        
        assert result is True
        mock_doc_ref.set.assert_called_once()
        
        # Verify placeholder flag is set
        call_args = mock_doc_ref.set.call_args[0][0]
        assert call_args['placeholder'] is True
        assert call_args['authenticated'] is False
        assert call_args['role'] == 'premium'
    
    def test_create_placeholder_existing_user_updates_role(self, firebase_service_available):
        """Test creating placeholder for existing user updates role"""
        # Mock get_user_by_email to return existing user
        firebase_service_available.get_user_by_email = Mock(return_value={'email': 'existing@example.com', 'role': 'free'})
        firebase_service_available.update_user_role = Mock(return_value=True)
        
        result = firebase_service_available.create_user_placeholder('existing@example.com', 'admin')
        
        assert result is True
        firebase_service_available.update_user_role.assert_called_once_with('existing@example.com', 'admin')


class TestUserRetrieval:
    """Test user retrieval methods"""
    
    def test_get_user_by_email_not_found(self, firebase_service_available, mock_firestore_client):
        """Test getting user by email when not found"""
        mock_doc = Mock()
        mock_doc.exists = False
        mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_doc
        
        result = firebase_service_available.get_user_by_email('notfound@example.com')
        assert result is None
    
    def test_get_user_by_email_found(self, firebase_service_available, mock_firestore_client):
        """Test getting user by email when found"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'email': 'found@example.com',
            'role': 'free',
            'name': 'Found User'
        }
        mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_doc
        
        result = firebase_service_available.get_user_by_email('found@example.com')
        
        assert result is not None
        assert result['email'] == 'found@example.com'
        assert result['role'] == 'free'
    
    def test_get_user_by_uid(self, firebase_service_available, mock_firestore_client):
        """Test getting user by UID"""
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {
            'uid': 'user_123',
            'email': 'user@example.com',
            'role': 'premium'
        }
        
        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc]
        mock_firestore_client.collection.return_value.where.return_value.limit.return_value = mock_query
        
        result = firebase_service_available.get_user_by_uid('user_123')
        
        assert result is not None
        assert result['uid'] == 'user_123'


class TestRoleManagement:
    """Test role update functionality"""
    
    def test_update_user_role_unavailable(self, firebase_service_unavailable):
        """Test role update when Firebase unavailable"""
        result = firebase_service_unavailable.update_user_role('test@example.com', 'premium')
        assert result is False
    
    def test_update_user_role_success(self, firebase_service_available, mock_firestore_client):
        """Test successful role update"""
        mock_doc_ref = Mock()
        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref
        
        result = firebase_service_available.update_user_role('user@example.com', 'admin')
        
        assert result is True
        mock_doc_ref.update.assert_called_once()
        call_args = mock_doc_ref.update.call_args[0][0]
        assert call_args['role'] == 'admin'
    
    def test_update_role_from_free_to_premium(self, firebase_service_available, mock_firestore_client):
        """Test upgrading from free to premium"""
        mock_doc_ref = Mock()
        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref
        
        result = firebase_service_available.update_user_role('user@example.com', 'premium')
        
        assert result is True


class TestUsageTracking:
    """Test usage tracking methods"""
    
    def test_increment_usage_count(self, firebase_service_available, mock_firestore_client):
        """Test incrementing usage count"""
        mock_doc_ref = Mock()
        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref
        
        with patch('firebase_admin.firestore.Increment') as mock_increment:
            mock_increment.return_value = "INCREMENT_VALUE"
            result = firebase_service_available.increment_usage_count('user@example.com')
        
        assert result is True
        mock_doc_ref.update.assert_called_once()
    
    def test_update_last_login(self, firebase_service_available, mock_firestore_client):
        """Test updating last login timestamp"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref
        
        result = firebase_service_available.update_user_last_login('user@example.com')
        
        assert result is True
        mock_doc_ref.update.assert_called_once()


class TestAdminFunctions:
    """Test admin-specific functions"""
    
    def test_get_all_users(self, firebase_service_available, mock_firestore_client):
        """Test retrieving all users"""
        mock_doc1 = Mock()
        mock_doc1.id = 'user1@example.com'
        mock_doc1.to_dict.return_value = {'email': 'user1@example.com', 'role': 'free'}
        
        mock_doc2 = Mock()
        mock_doc2.id = 'user2@example.com'
        mock_doc2.to_dict.return_value = {'email': 'user2@example.com', 'role': 'admin'}
        
        mock_firestore_client.collection.return_value.stream.return_value = [mock_doc1, mock_doc2]
        
        users = firebase_service_available.get_all_users()
        
        assert len(users) == 2
        assert users[0]['email'] == 'user1@example.com'
        assert users[1]['role'] == 'admin'
    
    def test_verify_admin_permission_true(self, firebase_service_available):
        """Test admin verification for admin user"""
        firebase_service_available.get_user_by_email = Mock(return_value={'email': 'admin@example.com', 'role': 'admin'})
        
        result = firebase_service_available.verify_admin_permission('admin@example.com')
        assert result is True
    
    def test_verify_admin_permission_false(self, firebase_service_available):
        """Test admin verification for non-admin user"""
        firebase_service_available.get_user_by_email = Mock(return_value={'email': 'user@example.com', 'role': 'free'})
        
        result = firebase_service_available.verify_admin_permission('user@example.com')
        assert result is False
    
    def test_verify_admin_permission_user_not_found(self, firebase_service_available):
        """Test admin verification when user not found"""
        firebase_service_available.get_user_by_email = Mock(return_value=None)
        firebase_service_available.get_user_by_uid = Mock(return_value=None)
        
        result = firebase_service_available.verify_admin_permission('notfound@example.com')
        assert result is False


class TestUserDeletion:
    """Test user deletion functionality"""
    
    def test_delete_user_success(self, firebase_service_available, mock_firestore_client):
        """Test successful user deletion"""
        mock_doc_ref = Mock()
        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref
        
        result = firebase_service_available.delete_user('user@example.com')
        
        assert result is True
        mock_doc_ref.delete.assert_called_once()
    
    def test_delete_user_unavailable(self, firebase_service_unavailable):
        """Test deletion when Firebase unavailable"""
        result = firebase_service_unavailable.delete_user('user@example.com')
        assert result is False


class TestAuditLogging:
    """Test audit logging functionality"""
    
    def test_log_admin_action_success(self, firebase_service_available, mock_firestore_client):
        """Test successful audit log creation"""
        mock_doc_ref = Mock()
        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref
        
        result = firebase_service_available.log_admin_action(
            admin_email='admin@example.com',
            action='role_change',
            target_user='user@example.com',
            details={'old_role': 'free', 'new_role': 'premium'},
            success=True
        )
        
        assert result is True
        mock_doc_ref.set.assert_called_once()
        
        # Verify log structure
        call_args = mock_doc_ref.set.call_args[0][0]
        assert call_args['admin_email'] == 'admin@example.com'
        assert call_args['action'] == 'role_change'
        assert call_args['target_user'] == 'user@example.com'
        assert call_args['success'] is True
        assert 'timestamp' in call_args
        assert 'session_id' in call_args
    
    def test_log_admin_action_unavailable(self, firebase_service_unavailable):
        """Test audit logging when Firebase unavailable"""
        result = firebase_service_unavailable.log_admin_action(
            admin_email='admin@example.com',
            action='role_change',
            target_user='user@example.com'
        )
        assert result is False
    
    def test_log_admin_action_with_failure(self, firebase_service_available, mock_firestore_client):
        """Test logging failed admin action"""
        mock_doc_ref = Mock()
        mock_firestore_client.collection.return_value.document.return_value = mock_doc_ref
        
        result = firebase_service_available.log_admin_action(
            admin_email='admin@example.com',
            action='user_deletion',
            target_user='user@example.com',
            details={'reason': 'User not found'},
            success=False
        )
        
        assert result is True
        call_args = mock_doc_ref.set.call_args[0][0]
        assert call_args['success'] is False
        assert call_args['details']['reason'] == 'User not found'


class TestGetAuditLogs:
    """Test audit log retrieval"""
    
    def test_get_audit_logs_basic(self, firebase_service_available, mock_firestore_client):
        """Test retrieving audit logs"""
        mock_doc1 = Mock()
        mock_doc1.to_dict.return_value = {
            'admin_email': 'admin@example.com',
            'action': 'role_change',
            'timestamp': datetime.now(timezone.utc)
        }
        
        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc1]
        mock_firestore_client.collection.return_value.order_by.return_value.limit.return_value = mock_query
        
        logs = firebase_service_available.get_audit_logs(limit=10)
        
        assert len(logs) == 1
        assert logs[0]['admin_email'] == 'admin@example.com'
    
    def test_get_audit_logs_unavailable(self, firebase_service_unavailable):
        """Test retrieving logs when Firebase unavailable"""
        logs = firebase_service_unavailable.get_audit_logs()
        assert logs == []

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from access_control.firebase_service import FirebaseService

@pytest.fixture
def mock_firestore():
    with patch('firebase_admin.firestore') as mock:
        yield mock

@pytest.fixture
def firebase_service(mock_firestore):
    service = FirebaseService()
    service._db = MagicMock()
    service._initialized = True
    return service

def test_get_audit_logs_client_side_filtering(firebase_service):
    """
    Test that get_audit_logs performs client-side filtering to avoid
    Firestore composite index requirements.
    """
    # Setup mock data
    mock_logs = [
        {
            'id': '1',
            'timestamp': datetime.now(),
            'admin_email': 'admin@example.com',
            'action': 'user_creation',
            'target_user': 'user1@example.com'
        },
        {
            'id': '2',
            'timestamp': datetime.now() - timedelta(hours=1),
            'admin_email': 'other@example.com',
            'action': 'role_change',
            'target_user': 'user2@example.com'
        },
        {
            'id': '3',
            'timestamp': datetime.now() - timedelta(hours=2),
            'admin_email': 'admin@example.com',
            'action': 'user_deletion',
            'target_user': 'user1@example.com'
        }
    ]

    # Mock the query stream to return these logs
    mock_stream = []
    for log in mock_logs:
        doc = MagicMock()
        doc.to_dict.return_value = log.copy()
        doc.id = log['id']
        mock_stream.append(doc)
    
    # Setup the query chain
    # We expect: collection -> order_by -> limit -> stream
    # We do NOT expect .where('admin_email', ...) etc.
    
    mock_collection = firebase_service.db.collection.return_value
    mock_query = mock_collection.order_by.return_value
    # Allow for date filters if present, but here we test without date filters first
    mock_query.limit.return_value.stream.return_value = mock_stream

    # Test 1: Filter by admin_email
    results = firebase_service.get_audit_logs(admin_filter='admin@example.com')
    
    # Verify results are filtered
    assert len(results) == 2
    assert results[0]['id'] == '1'
    assert results[1]['id'] == '3'
    
    # Verify the query did NOT use .where('admin_email', ...)
    # This is the crucial part to avoid index errors
    # We check all calls to .where()
    where_calls = mock_query.where.call_args_list
    for call in where_calls:
        args, _ = call
        field = args[0]
        assert field != 'admin_email', "Should not filter admin_email in Firestore query"

    # Test 2: Filter by action
    results = firebase_service.get_audit_logs(action_filter='role_change')
    assert len(results) == 1
    assert results[0]['id'] == '2'

    # Test 3: Filter by target_user
    results = firebase_service.get_audit_logs(target_user_filter='user1@example.com')
    assert len(results) == 2
    assert results[0]['id'] == '1'
    assert results[1]['id'] == '3'

    # Test 4: Combined filters
    results = firebase_service.get_audit_logs(
        admin_filter='admin@example.com',
        action_filter='user_creation'
    )
    assert len(results) == 1
    assert results[0]['id'] == '1'


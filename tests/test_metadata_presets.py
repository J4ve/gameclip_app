"""
Test metadata preset functionality with Firebase
Tests CRUD operations for user metadata presets stored in Firebase Firestore
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
from access_control.firebase_service import FirebaseService, get_firebase_service


class TestMetadataPresets:
    """Test metadata preset operations"""
    
    @pytest.fixture
    def mock_firestore_client(self):
        """Create a mock Firestore client"""
        mock_db = MagicMock()
        return mock_db
    
    @pytest.fixture
    def firebase_service(self, mock_firestore_client):
        """Create a FirebaseService instance with mocked Firestore"""
        with patch('firebase_admin.get_app') as mock_get_app:
            # Mock Firebase already initialized
            mock_get_app.return_value = MagicMock()
            
            with patch('firebase_admin.firestore.client') as mock_client:
                mock_client.return_value = mock_firestore_client
                
                service = FirebaseService()
                service._db = mock_firestore_client
                service._initialized = True
                
                return service
    
    @pytest.fixture
    def sample_preset_data(self):
        """Sample preset data for testing"""
        return {
            'name': 'Gaming Videos',
            'title': 'Epic Gaming Moments - {filename}',
            'description': 'Check out these amazing gaming highlights!\n\n#gaming #highlights',
            'tags': 'gaming, highlights, epic',
            'visibility': 'public',
            'made_for_kids': False,
            'metadata': {
                'created_from': 'config_tab',
                'video_type': 'gaming'
            }
        }
    
    def test_create_preset(self, firebase_service, mock_firestore_client, sample_preset_data):
        """Test creating a metadata preset"""
        # Setup mock
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = 'preset_123'
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection
        
        # Execute
        user_email = 'test@example.com'
        result = firebase_service.create_preset(user_email, sample_preset_data)
        
        # Verify
        assert result is not None
        assert result['id'] == 'preset_123'
        assert result['name'] == 'Gaming Videos'
        assert result['user_id'] == user_email
        assert 'created_at' in result
        assert 'updated_at' in result
        
        # Verify Firestore calls
        mock_firestore_client.collection.assert_called_once_with('metadata_presets')
        mock_doc_ref.set.assert_called_once()
    
    def test_create_preset_firebase_unavailable(self, firebase_service, sample_preset_data):
        """Test creating preset when Firebase is unavailable"""
        firebase_service._initialized = False
        
        with pytest.raises(Exception, match="Firebase not available"):
            firebase_service.create_preset('test@example.com', sample_preset_data)
    
    def test_get_user_presets(self, firebase_service, mock_firestore_client):
        """Test retrieving user presets"""
        # Setup mock documents
        mock_doc1 = MagicMock()
        mock_doc1.id = 'preset_1'
        mock_doc1.to_dict.return_value = {
            'name': 'Gaming Videos',
            'title': 'Gaming - {filename}',
            'user_id': 'test@example.com'
        }
        
        mock_doc2 = MagicMock()
        mock_doc2.id = 'preset_2'
        mock_doc2.to_dict.return_value = {
            'name': 'Tutorial Videos',
            'title': 'Tutorial - {filename}',
            'user_id': 'test@example.com'
        }
        
        # Setup mock query
        mock_query = MagicMock()
        mock_query.stream.return_value = [mock_doc1, mock_doc2]
        mock_where_result = MagicMock()
        mock_where_result.order_by.return_value = mock_query
        mock_collection = MagicMock()
        mock_collection.where.return_value = mock_where_result
        mock_firestore_client.collection.return_value = mock_collection
        
        # Execute
        user_email = 'test@example.com'
        presets = firebase_service.get_user_presets(user_email)
        
        # Verify
        assert len(presets) == 2
        assert presets[0]['id'] == 'preset_1'
        assert presets[0]['name'] == 'Gaming Videos'
        assert presets[1]['id'] == 'preset_2'
        assert presets[1]['name'] == 'Tutorial Videos'
        
        # Verify Firestore calls
        mock_firestore_client.collection.assert_called_once_with('metadata_presets')
        mock_collection.where.assert_called_once_with('user_id', '==', user_email)
    
    def test_get_user_presets_empty(self, firebase_service, mock_firestore_client):
        """Test retrieving presets when user has none"""
        # Setup mock query with no results
        mock_query = MagicMock()
        mock_query.stream.return_value = []
        mock_where_result = MagicMock()
        mock_where_result.order_by.return_value = mock_query
        mock_collection = MagicMock()
        mock_collection.where.return_value = mock_where_result
        mock_firestore_client.collection.return_value = mock_collection
        
        # Execute
        presets = firebase_service.get_user_presets('test@example.com')
        
        # Verify
        assert presets == []
    
    def test_get_user_presets_firebase_unavailable(self, firebase_service):
        """Test getting presets when Firebase is unavailable"""
        firebase_service._initialized = False
        
        presets = firebase_service.get_user_presets('test@example.com')
        assert presets == []
    
    def test_update_preset(self, firebase_service, mock_firestore_client):
        """Test updating a preset"""
        # Setup mock
        mock_doc_ref = MagicMock()
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection
        
        # Execute
        preset_id = 'preset_123'
        update_data = {
            'name': 'Updated Gaming Videos',
            'title': 'New Title - {filename}'
        }
        result = firebase_service.update_preset(preset_id, update_data)
        
        # Verify
        assert result is True
        mock_firestore_client.collection.assert_called_once_with('metadata_presets')
        mock_collection.document.assert_called_once_with(preset_id)
        mock_doc_ref.update.assert_called_once()
        
        # Check that updated_at was added
        call_args = mock_doc_ref.update.call_args[0][0]
        assert 'updated_at' in call_args
        assert call_args['name'] == 'Updated Gaming Videos'
    
    def test_update_preset_firebase_unavailable(self, firebase_service):
        """Test updating preset when Firebase is unavailable"""
        firebase_service._initialized = False
        
        result = firebase_service.update_preset('preset_123', {'name': 'Updated'})
        assert result is False
    
    def test_delete_preset(self, firebase_service, mock_firestore_client):
        """Test deleting a preset"""
        # Setup mock
        mock_doc_ref = MagicMock()
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection
        
        # Execute
        preset_id = 'preset_123'
        result = firebase_service.delete_preset(preset_id)
        
        # Verify
        assert result is True
        mock_firestore_client.collection.assert_called_once_with('metadata_presets')
        mock_collection.document.assert_called_once_with(preset_id)
        mock_doc_ref.delete.assert_called_once()
    
    def test_delete_preset_firebase_unavailable(self, firebase_service):
        """Test deleting preset when Firebase is unavailable"""
        firebase_service._initialized = False
        
        result = firebase_service.delete_preset('preset_123')
        assert result is False
    
    def test_get_preset_by_id(self, firebase_service, mock_firestore_client):
        """Test retrieving a specific preset by ID"""
        # Setup mock
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.id = 'preset_123'
        mock_doc.to_dict.return_value = {
            'name': 'Gaming Videos',
            'title': 'Gaming - {filename}',
            'user_id': 'test@example.com'
        }
        
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection
        
        # Execute
        preset = firebase_service.get_preset_by_id('preset_123')
        
        # Verify
        assert preset is not None
        assert preset['id'] == 'preset_123'
        assert preset['name'] == 'Gaming Videos'
        
        mock_firestore_client.collection.assert_called_once_with('metadata_presets')
        mock_collection.document.assert_called_once_with('preset_123')
    
    def test_get_preset_by_id_not_found(self, firebase_service, mock_firestore_client):
        """Test retrieving a preset that doesn't exist"""
        # Setup mock
        mock_doc = MagicMock()
        mock_doc.exists = False
        
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection
        
        # Execute
        preset = firebase_service.get_preset_by_id('nonexistent')
        
        # Verify
        assert preset is None
    
    def test_get_preset_by_id_firebase_unavailable(self, firebase_service):
        """Test getting preset by ID when Firebase is unavailable"""
        firebase_service._initialized = False
        
        preset = firebase_service.get_preset_by_id('preset_123')
        assert preset is None
    
    def test_create_preset_with_special_characters(self, firebase_service, mock_firestore_client):
        """Test creating preset with special characters in name"""
        # Setup mock
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = 'preset_special'
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.collection.return_value = mock_collection
        
        # Execute with special characters
        preset_data = {
            'name': 'Test @ #Preset! & More',
            'title': 'Title with émojis 🎮',
            'description': 'Description with\nmultiple\nlines',
            'tags': 'tag1, tag2, tag3',
            'visibility': 'unlisted',
            'made_for_kids': False
        }
        
        result = firebase_service.create_preset('test@example.com', preset_data)
        
        # Verify
        assert result is not None
        assert result['name'] == 'Test @ #Preset! & More'
        assert result['title'] == 'Title with émojis 🎮'
    
    def test_multiple_users_isolated_presets(self, firebase_service, mock_firestore_client):
        """Test that presets are isolated per user"""
        # Setup mock for user1
        mock_doc1 = MagicMock()
        mock_doc1.id = 'preset_user1'
        mock_doc1.to_dict.return_value = {
            'name': 'User1 Preset',
            'user_id': 'user1@example.com'
        }
        
        mock_query1 = MagicMock()
        mock_query1.stream.return_value = [mock_doc1]
        mock_where_result1 = MagicMock()
        mock_where_result1.order_by.return_value = mock_query1
        
        # Setup mock for user2
        mock_doc2 = MagicMock()
        mock_doc2.id = 'preset_user2'
        mock_doc2.to_dict.return_value = {
            'name': 'User2 Preset',
            'user_id': 'user2@example.com'
        }
        
        mock_query2 = MagicMock()
        mock_query2.stream.return_value = [mock_doc2]
        mock_where_result2 = MagicMock()
        mock_where_result2.order_by.return_value = mock_query2
        
        mock_collection = MagicMock()
        mock_collection.where.side_effect = [mock_where_result1, mock_where_result2]
        mock_firestore_client.collection.return_value = mock_collection
        
        # Execute
        presets_user1 = firebase_service.get_user_presets('user1@example.com')
        
        # Reset mock for second call
        mock_collection.where.side_effect = [mock_where_result2]
        presets_user2 = firebase_service.get_user_presets('user2@example.com')
        
        # Verify isolation
        assert len(presets_user1) == 1
        assert presets_user1[0]['user_id'] == 'user1@example.com'
        
        assert len(presets_user2) == 1
        assert presets_user2[0]['user_id'] == 'user2@example.com'


class TestMetadataPresetsIntegration:
    """Integration tests for metadata presets (require actual Firebase connection)"""
    
    @pytest.mark.integration
    def test_create_and_retrieve_preset_real_firebase(self):
        """Test creating and retrieving preset with real Firebase"""
        firebase = get_firebase_service()
        
        if not firebase or not firebase.is_available:
            pytest.skip("Firebase not available for integration test")
        
        # Create test preset
        test_email = f'test_{datetime.now().timestamp()}@example.com'
        preset_data = {
            'name': 'Integration Test Preset',
            'title': 'Test Title - {filename}',
            'description': 'Test description',
            'tags': 'test, integration',
            'visibility': 'private',
            'made_for_kids': False
        }
        
        # Create
        created_preset = firebase.create_preset(test_email, preset_data)
        assert created_preset is not None
        assert 'id' in created_preset
        preset_id = created_preset['id']
        
        try:
            # Retrieve - may fail if index not created yet
            try:
                retrieved_presets = firebase.get_user_presets(test_email)
                assert len(retrieved_presets) >= 1
                assert any(p['id'] == preset_id for p in retrieved_presets)
            except Exception as e:
                if 'index' in str(e).lower():
                    pytest.skip(f"Firebase index not created yet. See docs/FIREBASE_INDEXES.md")
                raise
            
            # Get by ID
            preset_by_id = firebase.get_preset_by_id(preset_id)
            assert preset_by_id is not None
            assert preset_by_id['name'] == 'Integration Test Preset'
            
        finally:
            # Cleanup
            firebase.delete_preset(preset_id)
    
    @pytest.mark.integration
    def test_update_preset_real_firebase(self):
        """Test updating preset with real Firebase"""
        firebase = get_firebase_service()
        
        if not firebase or not firebase.is_available:
            pytest.skip("Firebase not available for integration test")
        
        # Create test preset
        test_email = f'test_{datetime.now().timestamp()}@example.com'
        preset_data = {
            'name': 'Original Name',
            'title': 'Original Title',
            'description': 'Original description',
            'tags': 'original',
            'visibility': 'private',
            'made_for_kids': False
        }
        
        created_preset = firebase.create_preset(test_email, preset_data)
        preset_id = created_preset['id']
        
        try:
            # Update
            update_data = {
                'name': 'Updated Name',
                'title': 'Updated Title'
            }
            result = firebase.update_preset(preset_id, update_data)
            assert result is True
            
            # Verify update
            updated_preset = firebase.get_preset_by_id(preset_id)
            assert updated_preset['name'] == 'Updated Name'
            assert updated_preset['title'] == 'Updated Title'
            
        finally:
            # Cleanup
            firebase.delete_preset(preset_id)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

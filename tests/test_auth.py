"""
Unit tests for OAuth Authentication
Tests OAuth token handling and YouTube service creation (mocked)
"""

import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
import pickle
import os


class TestYouTubeService:
    """Test YouTubeService wrapper class"""
    
    def test_youtube_service_creation(self):
        """Test YouTubeService object creation"""
        from uploader.auth import YouTubeService
        
        mock_service = Mock()
        mock_credentials = Mock()
        
        yt_service = YouTubeService(mock_service, mock_credentials)
        
        assert yt_service.service == mock_service
        assert yt_service.credentials == mock_credentials


class TestTokenLoading:
    """Test token file loading and validation"""
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_load_existing_valid_token(self, mock_pickle_load, mock_file, mock_exists):
        """Test loading existing valid token"""
        mock_exists.return_value = True
        
        # Mock credentials
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ]
        mock_pickle_load.return_value = mock_creds
        
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_build.return_value = Mock()
            from uploader.auth import get_youtube_service
            
            service = get_youtube_service()
            
            assert service is not None
            assert service.credentials == mock_creds
    
    @patch('os.path.exists')
    def test_no_token_file_triggers_oauth(self, mock_exists):
        """Test that missing token file triggers OAuth flow"""
        mock_exists.return_value = False
        
        with patch('uploader.auth.InstalledAppFlow.from_client_secrets_file') as mock_flow_class:
            mock_flow = Mock()
            mock_flow_class.return_value = mock_flow
            
            mock_creds = Mock()
            mock_creds.valid = True
            mock_flow.run_local_server.return_value = mock_creds
            
            with patch('googleapiclient.discovery.build') as mock_build, \
                 patch('builtins.open', mock_open()):
                mock_build.return_value = Mock()
                
                from uploader.auth import get_youtube_service
                service = get_youtube_service()
                
                mock_flow.run_local_server.assert_called_once()
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_scope_mismatch_triggers_reauth(self, mock_pickle_load, mock_file, mock_exists):
        """Test that scope mismatch deletes token and triggers reauth"""
        mock_exists.return_value = True
        
        # Mock credentials with different scopes
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.scopes = ["https://www.googleapis.com/auth/youtube.upload"]  # Missing scopes
        mock_pickle_load.return_value = mock_creds
        
        with patch('os.remove') as mock_remove, \
             patch('uploader.auth.InstalledAppFlow.from_client_secrets_file') as mock_flow_class:
            
            mock_flow = Mock()
            mock_flow_class.return_value = mock_flow
            
            new_mock_creds = Mock()
            new_mock_creds.valid = True
            new_mock_creds.scopes = [
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email",
                "openid"
            ]
            mock_flow.run_local_server.return_value = new_mock_creds
            
            with patch('googleapiclient.discovery.build') as mock_build:
                mock_build.return_value = Mock()
                
                from uploader.auth import get_youtube_service
                service = get_youtube_service()
                
                # Should have deleted old token
                mock_remove.assert_called()


class TestTokenRefresh:
    """Test token refresh functionality"""
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_expired_token_refresh_success(self, mock_pickle_load, mock_file, mock_exists):
        """Test successful token refresh"""
        mock_exists.return_value = True
        
        # Mock expired but refreshable credentials
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token_123"
        mock_creds.scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ]
        mock_pickle_load.return_value = mock_creds
        
        with patch('google.auth.transport.requests.Request') as mock_request, \
             patch('googleapiclient.discovery.build') as mock_build:
            
            mock_build.return_value = Mock()
            
            # Simulate successful refresh
            def refresh_side_effect(request):
                mock_creds.valid = True
            
            mock_creds.refresh = Mock(side_effect=refresh_side_effect)
            
            from uploader.auth import get_youtube_service
            service = get_youtube_service()
            
            mock_creds.refresh.assert_called_once()
            assert service is not None
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_expired_token_refresh_failure(self, mock_pickle_load, mock_file, mock_exists):
        """Test token refresh failure triggers reauth"""
        mock_exists.return_value = True
        
        # Mock expired credentials that fail to refresh
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token_123"
        mock_creds.scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ]
        mock_creds.refresh = Mock(side_effect=Exception("Refresh failed"))
        mock_pickle_load.return_value = mock_creds
        
        with patch('os.remove') as mock_remove, \
             patch('uploader.auth.InstalledAppFlow.from_client_secrets_file') as mock_flow_class:
            
            mock_flow = Mock()
            mock_flow_class.return_value = mock_flow
            
            new_creds = Mock()
            new_creds.valid = True
            mock_flow.run_local_server.return_value = new_creds
            
            with patch('googleapiclient.discovery.build') as mock_build:
                mock_build.return_value = Mock()
                
                from uploader.auth import get_youtube_service
                service = get_youtube_service()
                
                # Should have triggered reauth
                mock_flow.run_local_server.assert_called_once()


class TestOAuthFlow:
    """Test OAuth 2.0 flow"""
    
    @patch('os.path.exists')
    @patch('uploader.auth.InstalledAppFlow.from_client_secrets_file')
    def test_oauth_flow_with_default_port(self, mock_flow_class, mock_exists):
        """Test OAuth flow uses default port 8080"""
        mock_exists.return_value = False
        
        mock_flow = Mock()
        mock_flow_class.return_value = mock_flow
        
        mock_creds = Mock()
        mock_creds.valid = True
        mock_flow.run_local_server.return_value = mock_creds
        
        with patch('googleapiclient.discovery.build') as mock_build, \
             patch('builtins.open', mock_open()):
            mock_build.return_value = Mock()
            
            from uploader.auth import get_youtube_service
            service = get_youtube_service()
            
            # Check that run_local_server was called with port 8080
            call_kwargs = mock_flow.run_local_server.call_args.kwargs
            assert call_kwargs['port'] == 8080
            assert call_kwargs['open_browser'] is True
    
    @patch('os.path.exists')
    @patch('uploader.auth.InstalledAppFlow.from_client_secrets_file')
    def test_oauth_flow_port_fallback(self, mock_flow_class, mock_exists):
        """Test OAuth flow falls back to alternative ports on failure"""
        mock_exists.return_value = False
        
        mock_flow = Mock()
        mock_flow_class.return_value = mock_flow
        
        # First port fails, second succeeds
        mock_creds = Mock()
        mock_creds.valid = True
        mock_flow.run_local_server.side_effect = [
            Exception("Port 8080 in use"),
            mock_creds  # Success on second try
        ]
        
        with patch('googleapiclient.discovery.build') as mock_build, \
             patch('builtins.open', mock_open()):
            mock_build.return_value = Mock()
            
            from uploader.auth import get_youtube_service
            service = get_youtube_service()
            
            # Should have tried twice
            assert mock_flow.run_local_server.call_count == 2


class TestTokenSaving:
    """Test token saving functionality"""
    
    @patch('os.path.exists')
    @patch('uploader.auth.InstalledAppFlow.from_client_secrets_file')
    def test_new_token_saved_after_auth(self, mock_flow_class, mock_exists):
        """Test that new tokens are saved to disk"""
        mock_exists.return_value = False
        
        mock_flow = Mock()
        mock_flow_class.return_value = mock_flow
        
        mock_creds = Mock()
        mock_creds.valid = True
        mock_flow.run_local_server.return_value = mock_creds
        
        with patch('googleapiclient.discovery.build') as mock_build, \
             patch('builtins.open', mock_open()) as m, \
             patch('pickle.dump') as mock_pickle_dump:
            
            mock_build.return_value = Mock()
            
            from uploader.auth import get_youtube_service
            service = get_youtube_service()
            
            # Verify pickle.dump was called to save credentials
            mock_pickle_dump.assert_called()


class TestScopeConfiguration:
    """Test OAuth scope configuration"""
    
    def test_scopes_include_youtube_upload(self):
        """Test that required YouTube upload scope is configured"""
        from uploader.auth import SCOPES
        assert "https://www.googleapis.com/auth/youtube.upload" in SCOPES
    
    def test_scopes_include_user_info(self):
        """Test that user info scopes are configured"""
        from uploader.auth import SCOPES
        assert "https://www.googleapis.com/auth/userinfo.profile" in SCOPES
        assert "https://www.googleapis.com/auth/userinfo.email" in SCOPES
    
    def test_scopes_include_openid(self):
        """Test that OpenID scope is configured"""
        from uploader.auth import SCOPES
        assert "openid" in SCOPES


class TestYouTubeServiceBuilding:
    """Test YouTube API service building"""
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_build_youtube_service_with_valid_creds(self, mock_pickle_load, mock_file, mock_exists):
        """Test building YouTube API service with valid credentials"""
        mock_exists.return_value = True
        
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ]
        mock_pickle_load.return_value = mock_creds
        
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_yt_service = Mock()
            mock_build.return_value = mock_yt_service
            
            from uploader.auth import get_youtube_service
            service = get_youtube_service()
            
            # Verify build was called with correct parameters
            mock_build.assert_called_once_with('youtube', 'v3', credentials=mock_creds)


class TestCorruptedTokenHandling:
    """Test handling of corrupted token files"""
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_corrupted_token_triggers_reauth(self, mock_pickle_load, mock_file, mock_exists):
        """Test that corrupted token file triggers reauth"""
        mock_exists.return_value = True
        mock_pickle_load.side_effect = Exception("Corrupted pickle file")
        
        with patch('os.remove') as mock_remove, \
             patch('uploader.auth.InstalledAppFlow.from_client_secrets_file') as mock_flow_class:
            
            mock_flow = Mock()
            mock_flow_class.return_value = mock_flow
            
            mock_creds = Mock()
            mock_creds.valid = True
            mock_flow.run_local_server.return_value = mock_creds
            
            with patch('googleapiclient.discovery.build') as mock_build:
                mock_build.return_value = Mock()
                
                from uploader.auth import get_youtube_service
                service = get_youtube_service()
                
                # Should have deleted corrupted token
                mock_remove.assert_called()
                # Should have triggered new auth
                mock_flow.run_local_server.assert_called_once()


class TestGetUserInfo:
    """Test user info retrieval from OAuth"""
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_get_user_info_from_credentials(self, mock_pickle_load, mock_file, mock_exists):
        """Test retrieving user info from credentials"""
        mock_exists.return_value = True
        
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ]
        mock_pickle_load.return_value = mock_creds
        
        with patch('googleapiclient.discovery.build') as mock_build, \
             patch('uploader.auth.build') as mock_oauth_build:
            
            # Mock YouTube service
            mock_yt_service = Mock()
            mock_build.return_value = mock_yt_service
            
            # Mock OAuth2 service
            mock_oauth_service = Mock()
            mock_oauth_build.return_value = mock_oauth_service
            
            mock_userinfo = Mock()
            mock_userinfo.get.return_value.execute.return_value = {
                'email': 'test@example.com',
                'name': 'Test User',
                'id': 'google_123',
                'picture': 'https://example.com/photo.jpg'
            }
            mock_oauth_service.userinfo.return_value = mock_userinfo
            
            from uploader.auth import get_youtube_service, get_user_info
            
            # Get service first
            service = get_youtube_service()
            
            # Get user info
            user_info = get_user_info(service.credentials)
            
            assert user_info['email'] == 'test@example.com'
            assert user_info['name'] == 'Test User'

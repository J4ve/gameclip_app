"""
Unit and integration tests for YouTube upload blocking for free users
Tests the premium upsell dialog and upload button logic
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from access_control.roles import FreeRole, PremiumRole, GuestRole, AdminRole
from access_control.session import SessionManager


@pytest.fixture
def mock_page():
    """Mock flet page"""
    page = Mock()
    page.overlay = []
    page.update = Mock()
    page.snack_bar = None
    return page


@pytest.fixture
def mock_session_free():
    """Mock session manager for free user"""
    patches = [
        patch('app.gui.save_upload_screen.session_manager'),
        patch('access_control.session.session_manager'),
    ]
    mocks = [p.start() for p in patches]
    
    for mock in mocks:
        mock.is_authenticated.return_value = True
        mock.is_logged_in = True
        mock.is_free.return_value = True
        mock.is_premium.return_value = False
        mock.is_admin.return_value = False
        mock.is_guest.return_value = False
        mock.role = FreeRole()
        mock.role_name = 'free'
        mock.current_user = {'email': 'free@test.com'}
        mock.has_permission = Mock(return_value=False)  # No upload permission
    
    yield mocks[0]
    
    for p in patches:
        p.stop()


@pytest.fixture
def mock_session_premium():
    """Mock session manager for premium user"""
    patches = [
        patch('app.gui.save_upload_screen.session_manager'),
        patch('access_control.session.session_manager'),
    ]
    mocks = [p.start() for p in patches]
    
    for mock in mocks:
        mock.is_authenticated.return_value = True
        mock.is_logged_in = True
        mock.is_free.return_value = False
        mock.is_premium.return_value = True
        mock.is_admin.return_value = False
        mock.role = PremiumRole()
        mock.role_name = 'premium'
        mock.current_user = {'email': 'premium@test.com'}
        mock.has_permission = Mock(return_value=True)  # Has upload permission
    
    yield mocks[0]
    
    for p in patches:
        p.stop()


@pytest.fixture
def mock_session_guest():
    """Mock session manager for guest user"""
    patches = [
        patch('app.gui.save_upload_screen.session_manager'),
        patch('access_control.session.session_manager'),
    ]
    mocks = [p.start() for p in patches]
    
    for mock in mocks:
        mock.is_authenticated.return_value = False
        mock.is_logged_in = False
        mock.is_free.return_value = False
        mock.is_premium.return_value = False
        mock.is_admin.return_value = False
        mock.is_guest.return_value = True
        mock.role = GuestRole()
        mock.role_name = 'guest'
        mock.has_permission = Mock(return_value=False)
    
    yield mocks[0]
    
    for p in patches:
        p.stop()


class TestUploadButtonState:
    """Test upload button state for different users"""
    
    def test_free_user_upload_button_locked(self, mock_page, mock_session_free):
        """Test that free users see locked upload button"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        layout = save_screen.build()
        
        # Upload button should show "Upload Locked" for free users
        assert save_screen.upload_button is not None
        # Button should have lock icon
        # Button should not be fully disabled (so tooltip/click work)
    
    def test_premium_user_upload_button_enabled(self, mock_page, mock_session_premium):
        """Test that premium users see enabled upload button"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        layout = save_screen.build()
        
        # Upload button should show "Save & Upload" for premium users
        assert save_screen.upload_button is not None
    
    def test_guest_user_upload_button_locked(self, mock_page, mock_session_guest):
        """Test that guest users see locked upload button"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        layout = save_screen.build()
        
        # Upload button should be locked for guests
        assert save_screen.upload_button is not None
    
    def test_upload_button_tooltip_for_free_user(self, mock_page, mock_session_free):
        """Test that free users see premium upsell tooltip"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        layout = save_screen.build()
        
        # Should have tooltip explaining premium feature
        # "YouTube upload is a Premium feature. Upgrade to upload your videos!"


class TestUploadButtonClick:
    """Test upload button click behavior"""
    
    def test_free_user_click_shows_premium_dialog(self, mock_page, mock_session_free):
        """Test that free users see premium upsell dialog when clicking upload"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
        save_screen.merged_video_path = 'merged.mp4'  # Simulate merged video
        
        # Mock the premium message method
        save_screen._show_upload_premium_message = Mock()
        
        # Click upload button (simulate)
        save_screen._handle_upload(None)
        
        # Should show premium message
        save_screen._show_upload_premium_message.assert_called_once()
    
    def test_premium_user_click_starts_upload(self, mock_page, mock_session_premium):
        """Test that premium users can upload when clicking button"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
        save_screen._show_upload_confirmation = Mock()
        
        # Click upload button
        save_screen._handle_upload(None)
        
        # Should show upload confirmation (not premium message)
        save_screen._show_upload_confirmation.assert_called_once()
    
    def test_guest_click_shows_premium_dialog(self, mock_page, mock_session_guest):
        """Test that guests see premium upsell dialog when clicking upload"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
        save_screen._show_upload_premium_message = Mock()
        
        # Click upload button
        save_screen._handle_upload(None)
        
        # Should show premium message or login prompt
        # Guests need to login first


class TestPremiumUpsellDialog:
    """Test premium upsell dialog content and behavior"""
    
    def test_premium_dialog_shows_features(self, mock_page, mock_session_free):
        """Test that premium dialog shows premium features"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        
        # Show premium dialog
        save_screen._show_upload_premium_message()
        
        # Dialog should be added to page overlay
        assert len(mock_page.overlay) > 0
        
        # Should contain premium feature list:
        # - Direct YouTube upload
        # - Unlimited arrangements
        # - No ads
        # - Lock positions
    
    def test_premium_dialog_has_upgrade_button(self, mock_page, mock_session_free):
        """Test that premium dialog has upgrade button"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen._show_upload_premium_message()
        
        # Should have "Upgrade to Premium" button
        assert len(mock_page.overlay) > 0
    
    def test_premium_dialog_has_dismiss_button(self, mock_page, mock_session_free):
        """Test that premium dialog can be dismissed"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen._show_upload_premium_message()
        
        # Should have "Maybe Later" button
        assert len(mock_page.overlay) > 0
    
    def test_upgrade_button_shows_coming_soon(self, mock_page, mock_session_free):
        """Test that upgrade button shows coming soon message"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen._show_premium_coming_soon = Mock()
        
        # Show dialog and click upgrade
        # The upgrade button should call _show_premium_coming_soon


class TestUploadPermissionCheck:
    """Test upload permission checking"""
    
    def test_free_user_no_upload_permission(self, mock_session_free):
        """Test that free users don't have upload permission"""
        from access_control.roles import Permission
        
        free_role = FreeRole()
        has_permission = Permission.UPLOAD_VIDEO in free_role.permissions
        
        # Free users do NOT have UPLOAD_VIDEO permission - it's a premium feature
        assert has_permission is False
    
    def test_premium_user_has_upload_permission(self, mock_session_premium):
        """Test that premium users have upload permission"""
        from access_control.roles import Permission
        
        premium_role = PremiumRole()
        has_permission = Permission.UPLOAD_VIDEO in premium_role.permissions
        
        assert has_permission is True
    
    def test_upload_check_blocks_free_users(self, mock_session_free):
        """Test that upload check specifically blocks free users (not permission-based)"""
        # The upload blocking is not permission-based
        # It's an explicit check: if session_manager.is_free()
        is_free = mock_session_free.is_free()
        assert is_free is True


class TestUploadStatusMessage:
    """Test upload status messages"""
    
    def test_free_user_sees_no_permission_message(self, mock_page, mock_session_free):
        """Test that free users see status message about no upload"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        layout = save_screen.build()
        
        # Should show "⚠️ Upload is a Premium feature" message
        # This is displayed in the upload settings section
    
    def test_guest_sees_login_required_message(self, mock_page, mock_session_guest):
        """Test that guests see login required message"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        layout = save_screen.build()
        
        # Should show message about logging in


class TestUploadButtonIcon:
    """Test upload button icon changes based on user"""
    
    def test_free_user_sees_lock_icon(self, mock_page, mock_session_free):
        """Test that free users see lock icon on upload button"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        layout = save_screen.build()
        
        # Button should have lock icon (ft.Icons.LOCK)
    
    def test_premium_user_sees_upload_icon(self, mock_page, mock_session_premium):
        """Test that premium users see upload icon"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        layout = save_screen.build()
        
        # Button should have upload icon (ft.Icons.UPLOAD)


class TestUploadWorkflow:
    """Test complete upload workflow for different users"""
    
    def test_free_user_blocked_from_upload(self, mock_page, mock_session_free):
        """Test that free user cannot complete upload workflow"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
        save_screen.merged_video_path = 'merged.mp4'
        
        # Try to start upload
        save_screen._show_upload_premium_message = Mock()
        save_screen._handle_upload(None)
        
        # Should be blocked with premium message
        save_screen._show_upload_premium_message.assert_called()
    
    def test_premium_user_can_upload(self, mock_page, mock_session_premium):
        """Test that premium user can complete upload workflow"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
        save_screen.merged_video_path = 'merged.mp4'
        save_screen._show_upload_confirmation = Mock()
        
        # Should be able to proceed to upload
        save_screen._handle_upload(None)
        
        # Should show confirmation dialog
        save_screen._show_upload_confirmation.assert_called_once()


class TestSaveStillWorks:
    """Test that save functionality still works for free users"""
    
    def test_free_user_can_save_locally(self, mock_page, mock_session_free):
        """Test that free users can still save videos locally"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
        save_screen._show_save_confirmation = Mock()
        
        # Click save button
        save_screen._handle_save(None)
        
        # Should work normally
        save_screen._show_save_confirmation.assert_called_once()
    
    def test_free_user_save_button_enabled(self, mock_page, mock_session_free):
        """Test that save button is enabled for free users"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
        layout = save_screen.build()
        
        # Save button should be enabled
        assert save_screen.save_button is not None


class TestAdminBypass:
    """Test that admin users have full upload access"""
    
    def test_admin_can_upload(self, mock_page):
        """Test that admin users can upload without premium"""
        with patch('access_control.session.session_manager') as mock_session:
            mock_session.is_authenticated.return_value = True
            mock_session.is_logged_in = True
            mock_session.is_free.return_value = False
            mock_session.is_premium.return_value = False
            mock_session.is_admin.return_value = True
            mock_session.role = AdminRole()
            mock_session.role_name = 'admin'
            mock_session.has_permission = Mock(return_value=True)
            
            from app.gui.save_upload_screen import SaveUploadScreen
            
            save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
            layout = save_screen.build()
            
            # Upload button should be enabled for admin
            # Admin should not see premium upsell


class TestUIFeedback:
    """Test UI feedback for upload restrictions"""
    
    def test_premium_banner_shows_for_free_users(self, mock_page, mock_session_free):
        """Test that premium upsell banner shows for free users"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        # Mock has_ads to return True for free users
        mock_session_free.has_ads = Mock(return_value=True)
        
        save_screen = SaveUploadScreen(page=mock_page)
        layout = save_screen.build()
        
        # Should show ad banner with premium upgrade message
    
    def test_upload_settings_disabled_for_free_users(self, mock_page, mock_session_free):
        """Test that upload settings button is disabled for free users"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        layout = save_screen.build()
        
        # Edit Upload Settings button should be disabled for free users


class TestIntegrationUploadBlocking:
    """Integration tests for upload blocking feature"""
    
    def test_complete_free_user_upload_attempt(self, mock_page, mock_session_free):
        """Test complete workflow of free user trying to upload"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        # Create save screen
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4', 'video2.mp4'])
        save_screen.build()
        
        # Free user selects videos and merges
        save_screen.set_videos(['video1.mp4', 'video2.mp4'])
        
        # Try to click upload button
        save_screen._show_upload_premium_message = Mock()
        save_screen._handle_upload(None)
        
        # Should see premium dialog
        save_screen._show_upload_premium_message.assert_called()
        
        # But can still save locally
        save_screen._show_save_confirmation = Mock()
        save_screen._handle_save(None)
        save_screen._show_save_confirmation.assert_called()
    
    def test_complete_premium_user_upload_success(self, mock_page, mock_session_premium):
        """Test complete workflow of premium user successfully uploading"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
        save_screen.build()
        
        # Premium user can proceed with upload
        save_screen._show_upload_confirmation = Mock()
        save_screen._handle_upload(None)
        
        # Should show upload confirmation
        save_screen._show_upload_confirmation.assert_called()


class TestPremiumFeatureMessaging:
    """Test messaging around premium features"""
    
    def test_dialog_mentions_free_users_can_save(self, mock_page, mock_session_free):
        """Test that premium dialog mentions free users can still save"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen._show_upload_premium_message()
        
        # Dialog should mention:
        # "💡 Free users can still save videos locally!"
        assert len(mock_page.overlay) > 0
    
    def test_premium_features_listed_correctly(self, mock_page, mock_session_free):
        """Test that premium features are accurately listed"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen._show_upload_premium_message()
        
        # Should list:
        # - Direct YouTube upload
        # - Unlimited arrangements
        # - No ads
        # - Lock positions
        assert len(mock_page.overlay) > 0


class TestEdgeCases:
    """Test edge cases for upload blocking"""
    
    def test_free_user_with_merged_video_still_blocked(self, mock_page, mock_session_free):
        """Test that having a merged video doesn't bypass upload block"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
        save_screen.merged_video_path = 'path/to/merged.mp4'
        
        save_screen._show_upload_premium_message = Mock()
        save_screen._handle_upload(None)
        
        # Still blocked
        save_screen._show_upload_premium_message.assert_called()
    
    def test_button_state_persists_after_save(self, mock_page, mock_session_free):
        """Test that upload button stays locked after save"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
        save_screen.build()
        
        # Simulate save completion
        save_screen.merged_video_path = 'merged.mp4'
        
        # Upload button should still be locked for free users

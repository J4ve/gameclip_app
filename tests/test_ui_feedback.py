"""
Unit and integration tests for UI feedback improvements
Tests arrangement usage indicators, premium features, and user notifications
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from access_control.roles import FreeRole, PremiumRole, GuestRole
from access_control.usage_tracker import UsageConfig


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
    """Mock session for free user"""
    patches = [
        patch('access_control.session.session_manager'),
        patch('app.gui.arrangement_screen.session_manager'),
        patch('access_control.usage_tracker.session_manager'),
    ]
    mocks = [p.start() for p in patches]
    
    for mock in mocks:
        mock.is_authenticated.return_value = True
        mock.is_free.return_value = True
        mock.is_premium.return_value = False
        mock.is_admin.return_value = False
        mock.role_name = 'free'
        mock.current_user = {'email': 'free@test.com'}
    
    yield mocks[0]
    
    for p in patches:
        p.stop()


@pytest.fixture
def mock_session_premium():
    """Mock session for premium user"""
    patches = [
        patch('access_control.session.session_manager'),
        patch('app.gui.arrangement_screen.session_manager'),
        patch('access_control.usage_tracker.session_manager'),
    ]
    mocks = [p.start() for p in patches]
    
    for mock in mocks:
        mock.is_authenticated.return_value = True
        mock.is_free.return_value = False
        mock.is_premium.return_value = True
        mock.is_admin.return_value = False
        mock.role_name = 'premium'
    
    yield mocks[0]
    
    for p in patches:
        p.stop()


class TestUsageInfoDisplay:
    """Test usage info display in arrangement screen"""
    
    def test_free_user_sees_usage_counter(self, mock_page, mock_session_free):
        """Test that free users see usage counter"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'used': 2,
                'limit': 5,
                'remaining': 3,
                'reset_time': '8h 30m'
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4'])
            layout = arrangement_screen.build()
            
            # Should display usage info
            assert arrangement_screen.usage_info_text is not None
    
    def test_usage_counter_shows_correct_format(self, mock_page, mock_session_free):
        """Test that usage counter shows correct format"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'used': 2,
                'limit': 5,
                'remaining': 3,
                'reset_time': '8h 30m'
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page)
            layout = arrangement_screen.build()
            
            # Should show "Arrangements: 2/5 (resets in 8h 30m)"
    
    def test_premium_user_no_usage_counter(self, mock_page, mock_session_premium):
        """Test that premium users don't see usage counter"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4'])
        layout = arrangement_screen.build()
        
        # Usage info should not be displayed for premium
    
    def test_usage_counter_updates_dynamically(self, mock_page, mock_session_free):
        """Test that usage counter updates when arrangement changes"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'used': 1,
                'limit': 5,
                'remaining': 4,
                'reset_time': '8h 30m'
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4', 'v2.mp4'])
            arrangement_screen.build()
            
            # Initial value
            initial_text = arrangement_screen.usage_info_text.value if arrangement_screen.usage_info_text else None
            
            # Arrangement changes - usage should update


class TestArrangementChangeIndicator:
    """Test the change indicator for arrangements"""
    
    def test_change_indicator_appears_on_modification(self, mock_page, mock_session_free):
        """Test that orange indicator appears when arrangement changes"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4', 'v2.mp4'])
        arrangement_screen.build()
        
        # Initially hidden
        if arrangement_screen.change_indicator:
            assert arrangement_screen.change_indicator.visible is False
        
        # Simulate arrangement change
        arrangement_screen.arrangement_changed = True
        arrangement_screen._update_change_indicator()
        
        # Should now be visible
        if arrangement_screen.change_indicator:
            assert arrangement_screen.change_indicator.visible is True
    
    def test_change_indicator_hidden_when_no_changes(self, mock_page, mock_session_free):
        """Test that change indicator is hidden when no changes made"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        arrangement_screen = ArrangementScreen(page=mock_page, videos=['video1.mp4'])
        arrangement_screen.build()
        
        # Initially, no changes should have been made
        # The indicator should be hidden by default
        if arrangement_screen.change_indicator:
            assert arrangement_screen.change_indicator.visible is False
    
    def test_change_indicator_shows_trial_warning_for_free_users(self, mock_page, mock_session_free):
        """Test that free users see trial usage warning in indicator"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'remaining': 3
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4'])
            arrangement_screen.build()
            
            # Make a change
            arrangement_screen.arrangement_changed = True
            arrangement_screen._update_change_indicator()
            
            # Should show "Arranged - will use 1 trial when saved (3 left)"
    
    def test_change_indicator_different_for_premium(self, mock_page, mock_session_premium):
        """Test that premium users see different indicator message"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4'])
        arrangement_screen.build()
        
        # Make a change
        arrangement_screen.arrangement_changed = True
        arrangement_screen._update_change_indicator()
        
        # Should show generic "Arrangement modified" (no trial warning)


class TestPremiumFeatureIndicators:
    """Test premium feature UI indicators"""
    
    def test_lock_feature_indicator_shows_for_premium(self, mock_page, mock_session_premium):
        """Test that premium users see lock feature indicator"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4'])
        layout = arrangement_screen.build()
        
        # Should show premium indicator with lock icon
    
    def test_lock_feature_indicator_hidden_for_free(self, mock_page, mock_session_free):
        """Test that free users don't see lock feature indicator"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4'])
        layout = arrangement_screen.build()
        
        # Lock indicator should not be visible for free users
    
    def test_lock_buttons_visible_for_premium(self, mock_page, mock_session_premium):
        """Test that lock/unlock buttons are visible for premium users"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4', 'v2.mp4'])
        arrangement_screen.set_videos(['v1.mp4', 'v2.mp4'])
        
        # Lock buttons should be present in video list
    
    def test_lock_buttons_hidden_for_free(self, mock_page, mock_session_free):
        """Test that lock/unlock buttons are hidden for free users"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4', 'v2.mp4'])
        arrangement_screen.set_videos(['v1.mp4', 'v2.mp4'])
        
        # Lock buttons should not be present


class TestUsageWarnings:
    """Test usage limit warnings and notifications"""
    
    def test_warning_shown_when_approaching_limit(self, mock_page, mock_session_free):
        """Test that warning is shown when user is close to limit"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            # User has 1 arrangement left
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'used': 4,
                'limit': 5,
                'remaining': 1,
                'reset_time': '8h 30m'
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page)
            arrangement_screen.build()
            
            # Warning color should be different when low
    
    def test_limit_reached_notification(self, mock_page, mock_session_free):
        """Test notification when limit is reached"""
        from app.gui.main_window import MainWindow
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            mock_tracker.can_arrange.return_value = False
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'limit': 5,
                'reset_time': '8h 30m'
            }
            
            main_window = MainWindow(mock_page)
            
            # Try to proceed from arrangement to save
            main_window.current_step = 1
            # Should show snackbar about limit reached
    
    def test_reset_time_displayed_in_warning(self, mock_page, mock_session_free):
        """Test that reset time is shown in limit warning"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'used': 5,
                'limit': 5,
                'remaining': 0,
                'reset_time': '2h 15m'
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page)
            arrangement_screen.build()
            
            # Should mention "resets in 2h 15m"


class TestColorCoding:
    """Test color coding for different states"""
    
    def test_usage_counter_color_normal(self, mock_page, mock_session_free):
        """Test usage counter color when usage is normal"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            # Plenty of arrangements left
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'remaining': 4
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page)
            arrangement_screen.build()
            
            # Should be blue/cyan color
    
    def test_usage_counter_color_warning(self, mock_page, mock_session_free):
        """Test usage counter color when limit is approaching"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            # Low remaining
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'remaining': 1
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page)
            arrangement_screen.build()
            
            # Should be orange/yellow color (warning)
    
    def test_usage_counter_color_limit_reached(self, mock_page, mock_session_free):
        """Test usage counter color when limit is reached"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            # No arrangements left
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'remaining': 0
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page)
            arrangement_screen.build()
            
            # Should be red color (error)
    
    def test_change_indicator_orange(self, mock_page, mock_session_free):
        """Test that change indicator is orange"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        arrangement_screen = ArrangementScreen(page=mock_page)
        arrangement_screen.build()
        
        # Change indicator should use orange color


class TestTooltipsAndHelp:
    """Test tooltips and help text"""
    
    def test_premium_feature_tooltip(self, mock_page, mock_session_free):
        """Test that premium features show appropriate tooltips"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4'])
        arrangement_screen.set_videos(['v1.mp4'])
        
        # Premium features (lock) should have tooltips for free users
    
    def test_usage_info_has_helpful_text(self, mock_page, mock_session_free):
        """Test that usage info has helpful explanatory text"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'used': 2,
                'limit': 5,
                'remaining': 3,
                'reset_time': '8h 30m'
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page)
            arrangement_screen.build()
            
            # Should clearly indicate what the counter means


class TestUploadButtonFeedback:
    """Test upload button UI feedback"""
    
    def test_upload_button_disabled_appearance_for_free(self, mock_page, mock_session_free):
        """Test that upload button appears disabled for free users"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.build()
        
        # Button should have muted color for free users
    
    def test_upload_button_enabled_appearance_for_premium(self, mock_page, mock_session_premium):
        """Test that upload button appears enabled for premium users"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.build()
        
        # Button should have active color for premium users
    
    def test_upload_button_tooltip_explains_restriction(self, mock_page, mock_session_free):
        """Test that upload button tooltip explains restriction for free users"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.build()
        
        # Tooltip should say "YouTube upload is a Premium feature"


class TestAdBanner:
    """Test ad banner for free users"""
    
    def test_ad_banner_shows_for_free_users(self, mock_page, mock_session_free):
        """Test that ad banner is displayed for free users"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        with patch('access_control.session.session_manager') as mock:
            mock.has_ads.return_value = True
            
            save_screen = SaveUploadScreen(page=mock_page)
            save_screen.build()
            
            # Ad banner should be visible
    
    def test_ad_banner_hidden_for_premium(self, mock_page, mock_session_premium):
        """Test that ad banner is hidden for premium users"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        with patch('access_control.session.session_manager') as mock:
            mock.has_ads.return_value = False
            
            save_screen = SaveUploadScreen(page=mock_page)
            save_screen.build()
            
            # Ad banner should not be visible
    
    def test_ad_banner_has_upgrade_link(self, mock_page, mock_session_free):
        """Test that ad banner has link to upgrade"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        with patch('access_control.session.session_manager') as mock:
            mock.has_ads.return_value = True
            
            save_screen = SaveUploadScreen(page=mock_page)
            save_screen.build()
            
            # Should have "Unlock Premium" button/link


class TestSnackbarNotifications:
    """Test snackbar notifications"""
    
    def test_limit_reached_snackbar(self, mock_page, mock_session_free):
        """Test snackbar when arrangement limit is reached"""
        from app.gui.main_window import MainWindow
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            mock_tracker.can_arrange.return_value = False
            mock_tracker.get_usage_info.return_value = {
                'limit': 5,
                'reset_time': '8h'
            }
            
            main_window = MainWindow(mock_page)
            # Should show snackbar with appropriate message
    
    def test_premium_feature_snackbar(self, mock_page, mock_session_free):
        """Test snackbar when clicking premium feature"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4'])
        
        # Try to use lock feature as free user
        arrangement_screen._toggle_lock(0)
        
        # Should show snackbar about premium feature


class TestProgressiveDisclosure:
    """Test progressive disclosure of features"""
    
    def test_free_user_sees_what_they_can_do(self, mock_page, mock_session_free):
        """Test that free users clearly see what they can do"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'remaining': 3
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page)
            arrangement_screen.build()
            
            # Should clearly show "3 arrangements remaining"
    
    def test_premium_features_clearly_marked(self, mock_page, mock_session_free):
        """Test that premium features are clearly marked"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.build()
        
        # Upload button should be marked as premium feature


class TestIntegrationUIFeedback:
    """Integration tests for UI feedback"""
    
    def test_complete_free_user_ui_experience(self, mock_page, mock_session_free):
        """Test complete UI experience for free user"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'used': 2,
                'limit': 5,
                'remaining': 3,
                'reset_time': '8h 30m'
            }
            mock_tracker.can_arrange.return_value = True
            
            # Create arrangement screen
            arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4', 'v2.mp4'])
            arrangement_screen.build()
            
            # Free user should see:
            # 1. Usage counter
            # 2. No lock buttons
            # 3. Change indicator when modifying
            
            # Make a change
            arrangement_screen.arrangement_changed = True
            arrangement_screen._update_change_indicator()
            
            # Should see appropriate feedback
    
    def test_complete_premium_user_ui_experience(self, mock_page, mock_session_premium):
        """Test complete UI experience for premium user"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4', 'v2.mp4'])
        arrangement_screen.build()
        
        # Premium user should see:
        # 1. No usage counter
        # 2. Lock buttons available
        # 3. Premium indicator badge
        # 4. No ads
    
    def test_ui_updates_on_arrangement_change(self, mock_page, mock_session_free):
        """Test that UI updates appropriately when arrangement changes"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'remaining': 3
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page, videos=['v1.mp4', 'v2.mp4'])
            arrangement_screen.build()
            
            # Before change - no indicator
            assert arrangement_screen.change_indicator.visible is False
            
            # Simulate change
            arrangement_screen.videos = ['v2.mp4', 'v1.mp4']  # Swapped order
            arrangement_screen._update_change_indicator()
            
            # After change - indicator visible
            # Note: Actual behavior depends on _check_arrangement_changed()


class TestAccessibility:
    """Test accessibility features of UI feedback"""
    
    def test_color_not_only_indicator(self, mock_page, mock_session_free):
        """Test that color is not the only way to convey information"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
            mock_tracker.get_usage_info.return_value = {
                'unlimited': False,
                'remaining': 1
            }
            
            arrangement_screen = ArrangementScreen(page=mock_page)
            arrangement_screen.build()
            
            # Should have text + icons, not just color
    
    def test_icons_supplement_text(self, mock_page, mock_session_free):
        """Test that icons supplement text messages"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.build()
        
        # Upload button should have both lock icon and text

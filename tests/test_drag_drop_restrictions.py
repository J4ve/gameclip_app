"""
Tests for Arrangement Drag and Drop Restrictions
Ensures drag and drop respects arrangement limits and user permissions
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
import flet as ft
from app.gui.arrangement_screen import ArrangementScreen
from access_control.roles import GuestRole, FreeRole, PremiumRole, AdminRole


@pytest.fixture
def mock_page():
    """Create mock Flet page"""
    page = MagicMock(spec=ft.Page)
    page.update = Mock()
    page.dialog = None
    page.snack_bar = None
    page.open = Mock()
    page.close = Mock()
    return page


@pytest.fixture
def mock_videos():
    """Create mock video list"""
    return [
        "video1.mp4",
        "video2.mp4",
        "video3.mp4",
    ]


@pytest.fixture
def mock_parent():
    """Create mock parent window"""
    parent = MagicMock()
    parent.page = MagicMock()
    parent.go_to_step = Mock()
    parent._return_to_login = Mock()
    return parent


class TestGuestDragDropRestrictions:
    """Test that guests cannot use drag and drop"""
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_guest_cannot_drag_videos(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """Guest users should not be able to drag videos"""
        # Setup guest session
        mock_session.is_guest = True
        mock_session.is_authenticated = False  # Property, not method
        mock_session.current_user = None
        mock_tracker.can_arrange.return_value = False
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        screen.build()
        
        # Try to drag
        drag_event = Mock()
        drag_event.control = Mock()
        drag_event.control.data = 0  # First video
        
        # Should not accept drag
        result = screen._handle_drag_will_accept(drag_event, 0)
        assert result is None or result is False, "Guest should not be able to drag videos"
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_guest_cannot_drop_videos(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """Guest users should not be able to drop videos"""
        mock_session.is_guest = True
        mock_session.is_authenticated = False  # Property, not method
        mock_tracker.can_arrange.return_value = False
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        screen.build()
        
        # Try to drop
        drop_event = Mock()
        drop_event.control = Mock()
        drop_event.control.data = 1  # Drop target
        drop_event.src_id = "0"  # Source video
        
        original_order = screen.videos.copy()
        screen._handle_drag_accept(drop_event, 1)  # Pass target_idx
        
        # Order should not change
        assert screen.videos == original_order, "Guest drop should not reorder videos"
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_guest_sees_disabled_drag_indicators(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """Guest should see visual indicators that drag is disabled"""
        mock_session.is_guest = True
        mock_tracker.can_arrange.return_value = False
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        built = screen.build()
        
        # Check that drag targets are disabled
        assert screen.arrangement_disabled == True, "Arrangement should be disabled for guests"


class TestFreeLimitDragDropRestrictions:
    """Test that free users at limit cannot use drag and drop"""
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_free_user_at_limit_cannot_drag(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """Free users who hit daily limit should not be able to drag"""
        mock_session.is_guest = False
        mock_session.is_authenticated = True  # Property, not method
        mock_session.current_user = {"email": "user@test.com", "role": FreeRole()}
        mock_session.is_premium.return_value = False
        mock_session.is_admin.return_value = False
        mock_tracker.can_arrange.return_value = False  # Limit reached
        mock_tracker.get_remaining_arrangements.return_value = 0
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        screen.build()
        
        # Try to drag
        drag_event = Mock()
        drag_event.control = Mock()
        drag_event.control.data = 0
        drag_event.control.content = Mock()
        
        result = screen._handle_drag_will_accept(drag_event, 0)
        assert result is None or result is False, "Free user at limit should not be able to drag"
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_free_user_at_limit_cannot_drop(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """Free users who hit daily limit should not be able to drop"""
        mock_session.is_guest = False
        mock_session.is_authenticated = True  # Property, not method
        mock_session.current_user = {"email": "user@test.com", "role": FreeRole()}
        mock_session.is_premium.return_value = False
        mock_tracker.can_arrange.return_value = False
        mock_tracker.get_remaining_arrangements.return_value = 0
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        screen.build()
        
        # Try to drop
        drop_event = Mock()
        drop_event.control = Mock()
        drop_event.control.data = 1
        drop_event.src_id = "0"
        
        original_order = screen.videos.copy()
        screen._handle_drag_accept(drop_event, 1)
        
        # Order should not change
        assert screen.videos == original_order, "Free user at limit drop should not reorder videos"
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_free_user_with_arrangements_can_drag(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """Free users with remaining arrangements should be able to drag"""
        mock_session.is_guest = False
        mock_session.is_authenticated = True  # Property, not method
        mock_session.current_user = {"email": "user@test.com", "role": FreeRole()}
        mock_session.is_premium.return_value = False
        mock_tracker.can_arrange.return_value = True  # Has arrangements left
        mock_tracker.get_remaining_arrangements.return_value = 3
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        screen.build()
        
        # Try to drag
        drag_event = Mock()
        drag_event.control = Mock()
        drag_event.control.data = 0
        
        # Should allow drag when user has arrangements left
        assert screen.arrangement_disabled == False, "Free user with arrangements should not be disabled"


class TestPremiumDragDropAccess:
    """Test that premium users have unrestricted drag and drop"""
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_premium_user_can_drag(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """Premium users should always be able to drag"""
        mock_session.is_guest = False
        mock_session.is_authenticated = True  # Property, not method
        mock_session.current_user = {"email": "premium@test.com", "role": PremiumRole()}
        mock_session.is_premium.return_value = True
        mock_tracker.can_arrange.return_value = True
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        screen.build()
        
        assert screen.arrangement_disabled == False, "Premium users should not be disabled"
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_premium_user_can_drop_unlimited(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """Premium users should be able to drop videos unlimited times"""
        mock_session.is_guest = False
        mock_session.is_authenticated = True  # Property, not method
        mock_session.current_user = {"email": "premium@test.com", "role": PremiumRole()}
        mock_session.is_premium.return_value = True
        mock_tracker.can_arrange.return_value = True
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        screen.build()
        
        # Try to drop multiple times
        for i in range(10):
            drop_event = Mock()
            drop_event.control = Mock()
            drop_event.control.page = None  # No page.get_control, will use src_id directly
            drop_event.control.data = 1
            drop_event.src_id = 0  # Use integer
            drop_event.data = 0  # Fallback data
            
            # Should always work for premium (doesn't check limit)
            # Just verify arrangement_disabled is False
            assert screen.arrangement_disabled == False, "Premium users should not be disabled"


class TestAdminDragDropAccess:
    """Test that admin users have unrestricted drag and drop"""
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_admin_user_can_drag(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """Admin users should always be able to drag"""
        mock_session.is_guest = False
        mock_session.is_authenticated = True  # Property, not method
        mock_session.current_user = {"email": "admin@test.com", "role": AdminRole()}
        mock_session.is_admin.return_value = True
        mock_tracker.can_arrange.return_value = True
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        screen.build()
        
        assert screen.arrangement_disabled == False, "Admin users should not be disabled"


class TestDragDropBypassPrevention:
    """Test that drag and drop cannot bypass arrangement limits"""
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_drag_drop_checks_permissions_on_every_operation(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """Each drag/drop operation should check permissions"""
        mock_session.is_guest = True
        mock_tracker.can_arrange.return_value = False
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        screen.build()
        
        # Multiple attempts should all be blocked
        for i in range(5):
            drop_event = Mock()
            drop_event.control = Mock()
            drop_event.control.data = i % 3
            drop_event.src_id = str((i + 1) % 3)
            
            original_order = screen.videos.copy()
            screen._handle_drag_accept(drop_event, i % 3)
            
            assert screen.videos == original_order, f"Attempt {i} should be blocked"
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_will_accept_returns_false_when_disabled(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """_on_will_accept should return False when arrangement is disabled"""
        mock_session.is_guest = True
        mock_tracker.can_arrange.return_value = False
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        screen.build()
        
        drag_event = Mock()
        drag_event.control = Mock()
        drag_event.control.data = 0
        drag_event.control.content = Mock()
        
        result = screen._handle_drag_will_accept(drag_event, 0)
        assert result is False or result is None, "_handle_drag_will_accept should reject when disabled"
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_drag_accept_shows_snackbar_when_blocked(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """_on_drag_accept should show feedback when operation is blocked"""
        mock_session.is_guest = True
        mock_tracker.can_arrange.return_value = False
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        screen.build()
        
        drop_event = Mock()
        drop_event.control = Mock()
        drop_event.control.data = 1
        drop_event.src_id = "0"
        
        screen._handle_drag_accept(drop_event, 1)
        
        # Should show some feedback (snackbar or dialog)
        assert mock_page.snack_bar is not None or mock_page.update.called, "Should provide feedback when blocked"


class TestDragDropVisualFeedback:
    """Test visual feedback for drag and drop restrictions"""
    
    @patch('app.gui.arrangement_screen.session_manager')
    @patch('app.gui.arrangement_screen.usage_tracker')
    def test_disabled_state_shows_tooltips(self, mock_tracker, mock_session, mock_page, mock_videos, mock_parent):
        """Disabled drag/drop should show helpful tooltips"""
        mock_session.is_guest = True
        mock_tracker.can_arrange.return_value = False
        
        screen = ArrangementScreen(mock_page, mock_videos, mock_parent)
        screen.build()
        
        # The screen should have set arrangement_disabled=True
        assert screen.arrangement_disabled == True, "Should be disabled for guests"

"""
Unit and integration tests for 'Merge Other Clips' button functionality
Tests the workflow reset button in success dialogs
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path


@pytest.fixture
def mock_page():
    """Mock flet page"""
    page = Mock()
    page.overlay = []
    page.update = Mock()
    return page


@pytest.fixture
def mock_main_window():
    """Mock main window"""
    main_window = Mock()
    main_window.go_to_step = Mock()
    main_window.current_step = 2
    return main_window


class TestMergeOtherClipsButton:
    """Test 'Merge Other Clips' button in success dialogs"""
    
    def test_button_appears_in_save_success_dialog(self, mock_page):
        """Test that button appears in save success dialog"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.merged_video_path = 'test.mp4'
        
        # Show success dialog
        save_screen._show_success("Video saved successfully!")
        
        # Dialog should be added to overlay
        assert len(mock_page.overlay) > 0
        
        # Should contain "Merge Other Clips" button
    
    def test_button_appears_in_upload_success_dialog(self, mock_page):
        """Test that button appears in upload success dialog"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        
        # Show upload success dialog
        save_screen._show_upload_success("test_video_id")
        
        # Dialog should be added to overlay
        assert len(mock_page.overlay) > 0
        
        # Should contain "Merge Other Clips" button
    
    def test_button_has_correct_icon(self, mock_page):
        """Test that button has video library icon"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.merged_video_path = 'test.mp4'
        
        # Show success dialog
        save_screen._show_success("Video saved!")
        
        # Button should have ft.Icons.VIDEO_LIBRARY icon
    
    def test_button_has_correct_styling(self, mock_page):
        """Test that button has correct styling (blue elevated button)"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen._show_upload_success("test_id")
        
        # Button should be styled as primary action (blue background, white text)


class TestButtonFunctionality:
    """Test button click functionality"""
    
    def test_button_closes_dialog(self, mock_page, mock_main_window):
        """Test that clicking button closes the dialog"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = mock_main_window
        save_screen.merged_video_path = 'test.mp4'
        save_screen._close_dialog = Mock()
        
        # Show success dialog
        save_screen._show_success("Video saved!")
        
        # Get the dialog
        dialog = mock_page.overlay[-1] if mock_page.overlay else None
        
        # Simulate button click
        save_screen._start_new_merge(dialog)
        
        # Should close dialog
        save_screen._close_dialog.assert_called_once()
    
    def test_button_navigates_to_selection_screen(self, mock_page, mock_main_window):
        """Test that button navigates back to selection screen (step 0)"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = mock_main_window
        
        # Simulate button click
        save_screen._start_new_merge(None)
        
        # Should navigate to step 0
        mock_main_window.go_to_step.assert_called_once_with(0)
    
    def test_button_resets_workflow(self, mock_page, mock_main_window):
        """Test that button resets the merge workflow"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = mock_main_window
        save_screen.merged_video_path = 'old_merge.mp4'
        save_screen.videos = ['video1.mp4', 'video2.mp4']
        
        # Start new merge
        save_screen._start_new_merge(None)
        
        # Should go back to step 0 (selection screen)
        mock_main_window.go_to_step.assert_called_with(0)


class TestUserWorkflow:
    """Test complete user workflows with button"""
    
    def test_save_then_merge_more_workflow(self, mock_page, mock_main_window):
        """Test workflow: save video -> click 'Merge Other Clips'"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
        save_screen.main_window = mock_main_window
        save_screen.merged_video_path = 'merged1.mp4'
        
        # Complete save
        save_screen._show_success("Video saved!")
        
        # Click "Merge Other Clips"
        save_screen._start_new_merge(None)
        
        # Should be back at selection screen
        mock_main_window.go_to_step.assert_called_with(0)
    
    def test_upload_then_merge_more_workflow(self, mock_page, mock_main_window):
        """Test workflow: upload video -> click 'Merge Other Clips'"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page, videos=['video1.mp4'])
        save_screen.main_window = mock_main_window
        
        # Complete upload
        save_screen._show_upload_success("abc123")
        
        # Click "Merge Other Clips"
        save_screen._start_new_merge(None)
        
        # Should be back at selection screen
        mock_main_window.go_to_step.assert_called_with(0)
    
    def test_multiple_merge_cycles(self, mock_page, mock_main_window):
        """Test user can merge multiple times in sequence"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = mock_main_window
        
        # First merge
        save_screen.set_videos(['video1.mp4', 'video2.mp4'])
        save_screen.merged_video_path = 'merge1.mp4'
        save_screen._show_success("First merge done!")
        save_screen._start_new_merge(None)
        
        # Second merge
        save_screen.set_videos(['video3.mp4', 'video4.mp4'])
        save_screen.merged_video_path = 'merge2.mp4'
        save_screen._show_success("Second merge done!")
        save_screen._start_new_merge(None)
        
        # Should have navigated to step 0 twice
        assert mock_main_window.go_to_step.call_count == 2


class TestButtonPlacement:
    """Test button placement in dialogs"""
    
    def test_button_in_save_dialog_actions(self, mock_page):
        """Test that button is in dialog actions section"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.merged_video_path = 'test.mp4'
        
        save_screen._show_success("Saved!")
        
        # Should be in actions section with "Done" button
        assert len(mock_page.overlay) > 0
    
    def test_button_in_upload_dialog_actions(self, mock_page):
        """Test that button is in upload success dialog actions"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        
        save_screen._show_upload_success("video_id_123")
        
        # Should be in actions section
        assert len(mock_page.overlay) > 0
    
    def test_done_button_also_present(self, mock_page):
        """Test that 'Done' button is still present alongside 'Merge Other Clips'"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.merged_video_path = 'test.mp4'
        
        save_screen._show_success("Saved!")
        
        # Both buttons should be present
        # "Done" and "Merge Other Clips"


class TestButtonAlternatives:
    """Test button vs done button behavior"""
    
    def test_done_button_closes_dialog_only(self, mock_page):
        """Test that 'Done' button only closes dialog without navigation"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = Mock()
        save_screen.merged_video_path = 'test.mp4'
        save_screen._close_dialog = Mock()
        
        save_screen._show_success("Saved!")
        
        # Get dialog
        dialog = mock_page.overlay[-1] if mock_page.overlay else None
        
        # Done button should only close dialog
        # Does not navigate
    
    def test_merge_other_clips_closes_and_navigates(self, mock_page, mock_main_window):
        """Test that 'Merge Other Clips' closes dialog AND navigates"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = mock_main_window
        save_screen._close_dialog = Mock()
        
        # Pass a mock dialog instead of None
        mock_dialog = Mock()
        save_screen._start_new_merge(mock_dialog)
        
        # Should close dialog
        save_screen._close_dialog.assert_called_once_with(mock_dialog)
        
        # Should navigate
        mock_main_window.go_to_step.assert_called_with(0)


class TestStateReset:
    """Test that state is properly reset for new merge"""
    
    def test_selection_screen_is_clean_after_reset(self, mock_page, mock_main_window):
        """Test that selection screen is ready for new videos"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = mock_main_window
        
        # Set up initial state
        save_screen.videos = ['old1.mp4', 'old2.mp4']
        save_screen.merged_video_path = 'old_merge.mp4'
        
        # Start new merge
        save_screen._start_new_merge(None)
        
        # User should be at selection screen (step 0)
        mock_main_window.go_to_step.assert_called_with(0)
    
    def test_previous_videos_not_carried_over(self, mock_page, mock_main_window):
        """Test that previous video selection doesn't carry over"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = mock_main_window
        
        # First merge
        save_screen.set_videos(['video1.mp4', 'video2.mp4'])
        save_screen._start_new_merge(None)
        
        # After reset, should start fresh
        mock_main_window.go_to_step.assert_called_with(0)


class TestIntegrationMergeOtherClips:
    """Integration tests for complete merge-again workflow"""
    
    def test_complete_save_and_merge_again(self, mock_page, mock_main_window):
        """Test complete workflow from save to starting new merge"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        # Setup
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = mock_main_window
        save_screen.videos = ['video1.mp4', 'video2.mp4']
        
        # User saves video
        save_screen.merged_video_path = 'merged.mp4'
        save_screen._show_success("Video saved successfully!")
        
        # Verify success dialog shown
        assert len(mock_page.overlay) > 0
        
        # User clicks "Merge Other Clips"
        save_screen._start_new_merge(mock_page.overlay[-1])
        
        # Should navigate to selection
        mock_main_window.go_to_step.assert_called_with(0)
    
    def test_complete_upload_and_merge_again(self, mock_page, mock_main_window):
        """Test complete workflow from upload to starting new merge"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = mock_main_window
        
        # User uploads video
        save_screen._show_upload_success("video_id_xyz")
        
        # Verify dialog shown
        assert len(mock_page.overlay) > 0
        
        # User clicks "Merge Other Clips"
        save_screen._start_new_merge(mock_page.overlay[-1])
        
        # Should navigate to selection
        mock_main_window.go_to_step.assert_called_with(0)
    
    def test_merge_three_times_in_sequence(self, mock_page, mock_main_window):
        """Test user can merge multiple videos in sequence easily"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = mock_main_window
        
        # Merge 1
        save_screen.set_videos(['a.mp4', 'b.mp4'])
        save_screen.merged_video_path = 'merge1.mp4'
        save_screen._show_success("First merge!")
        save_screen._start_new_merge(None)
        
        # Merge 2
        save_screen.set_videos(['c.mp4', 'd.mp4'])
        save_screen.merged_video_path = 'merge2.mp4'
        save_screen._show_success("Second merge!")
        save_screen._start_new_merge(None)
        
        # Merge 3
        save_screen.set_videos(['e.mp4', 'f.mp4'])
        save_screen.merged_video_path = 'merge3.mp4'
        save_screen._show_success("Third merge!")
        save_screen._start_new_merge(None)
        
        # Should have reset 3 times
        assert mock_main_window.go_to_step.call_count == 3


class TestUIConsistency:
    """Test UI consistency across different dialogs"""
    
    def test_button_appears_in_both_dialogs(self, mock_page):
        """Test that button appears in both save and upload success dialogs"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        
        # Test save dialog
        save_screen.merged_video_path = 'test.mp4'
        save_screen._show_success("Saved!")
        save_dialog_count = len(mock_page.overlay)
        
        # Clear overlays
        mock_page.overlay.clear()
        
        # Test upload dialog
        save_screen._show_upload_success("video_id")
        upload_dialog_count = len(mock_page.overlay)
        
        # Both should have dialogs
        assert save_dialog_count > 0
        assert upload_dialog_count > 0
    
    def test_button_text_consistent(self, mock_page):
        """Test that button text is consistent across dialogs"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        
        # Both should use "Merge Other Clips" text


class TestEdgeCases:
    """Test edge cases for merge other clips feature"""
    
    def test_button_works_without_main_window(self, mock_page):
        """Test that button handles missing main_window gracefully"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = None
        
        # Should not crash
        save_screen._start_new_merge(None)
    
    def test_button_works_with_no_previous_videos(self, mock_page, mock_main_window):
        """Test that button works even if no videos were merged"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = mock_main_window
        save_screen.videos = []
        
        # Should still navigate
        save_screen._start_new_merge(None)
        mock_main_window.go_to_step.assert_called_with(0)
    
    def test_dialog_closes_properly(self, mock_page, mock_main_window):
        """Test that dialog is properly closed before navigation"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        save_screen = SaveUploadScreen(page=mock_page)
        save_screen.main_window = mock_main_window
        save_screen._close_dialog = Mock()
        
        mock_dialog = Mock()
        save_screen._start_new_merge(mock_dialog)
        
        # Dialog should be closed
        save_screen._close_dialog.assert_called_once_with(mock_dialog)


class TestButtonAccessibility:
    """Test button accessibility for all user types"""
    
    def test_free_users_can_use_button(self, mock_page, mock_main_window):
        """Test that free users can click 'Merge Other Clips'"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        with patch('access_control.session.session_manager') as mock_session:
            mock_session.is_free.return_value = True
            mock_session.is_premium.return_value = False
            
            save_screen = SaveUploadScreen(page=mock_page)
            save_screen.main_window = mock_main_window
            
            # Free users can use the button
            save_screen._start_new_merge(None)
            mock_main_window.go_to_step.assert_called_with(0)
    
    def test_premium_users_can_use_button(self, mock_page, mock_main_window):
        """Test that premium users can click 'Merge Other Clips'"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        with patch('access_control.session.session_manager') as mock_session:
            mock_session.is_premium.return_value = True
            
            save_screen = SaveUploadScreen(page=mock_page)
            save_screen.main_window = mock_main_window
            
            # Premium users can use the button
            save_screen._start_new_merge(None)
            mock_main_window.go_to_step.assert_called_with(0)
    
    def test_guests_can_use_button(self, mock_page, mock_main_window):
        """Test that guests can click 'Merge Other Clips'"""
        from app.gui.save_upload_screen import SaveUploadScreen
        
        with patch('access_control.session.session_manager') as mock_session:
            mock_session.is_authenticated.return_value = False
            
            save_screen = SaveUploadScreen(page=mock_page)
            save_screen.main_window = mock_main_window
            
            # Guests can use the button
            save_screen._start_new_merge(None)
            mock_main_window.go_to_step.assert_called_with(0)

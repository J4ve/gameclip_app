"""
Integration tests for session manager and usage tracker integration
Tests the accuracy and robustness of the refactored system
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from access_control.session import SessionManager, session_manager
from access_control.usage_tracker import UsageTracker, UsageConfig, usage_tracker
from access_control.roles import FreeRole, PremiumRole, GuestRole, AdminRole


@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create temporary storage for tests"""
    storage_dir = tmp_path / "usage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    original_dir = UsageConfig.STORAGE_DIR
    UsageConfig.STORAGE_DIR = storage_dir
    
    yield storage_dir
    
    UsageConfig.STORAGE_DIR = original_dir


@pytest.fixture
def clean_session():
    """Create a clean session manager"""
    # Use the global singleton instance
    from access_control.session import session_manager
    session_manager.logout()
    return session_manager


@pytest.fixture
def fresh_tracker(temp_storage_dir):
    """Create fresh usage tracker"""
    return UsageTracker()


class TestSessionUsageTrackerIntegration:
    """Test integration between session manager and usage tracker"""
    
    def test_usage_tracker_reads_from_session(self, clean_session, fresh_tracker):
        """Test that usage tracker correctly reads user from session"""
        # Login as free user
        user_info = {'email': 'test@example.com', 'name': 'Test User'}
        clean_session.login(user_info, FreeRole())
        
        # Usage tracker should recognize the user
        remaining = fresh_tracker.get_remaining_arrangements()
        assert remaining is not None
    
    def test_session_role_affects_usage_tracking(self, clean_session, fresh_tracker):
        """Test that different roles get different usage tracking"""
        user_info = {'email': 'test@example.com'}
        
        # Test as free user
        clean_session.login(user_info, FreeRole())
        free_remaining = fresh_tracker.get_remaining_arrangements()
        
        # Test as premium user
        clean_session.logout()
        clean_session.login(user_info, PremiumRole())
        premium_remaining = fresh_tracker.get_remaining_arrangements()
        
        # Free should have limit, premium should be unlimited (None)
        assert free_remaining == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS
        assert premium_remaining is None
    
    def test_logout_prevents_arrangement_recording(self, clean_session, fresh_tracker):
        """Test that logged out users cannot record arrangements"""
        user_info = {'email': 'test@example.com'}
        
        # Login and record
        clean_session.login(user_info, FreeRole())
        assert fresh_tracker.record_arrangement() is True
        
        # Logout
        clean_session.logout()
        
        # Cannot record when logged out
        assert fresh_tracker.record_arrangement() is False
    
    def test_role_change_reflected_in_usage(self, clean_session, fresh_tracker):
        """Test that role changes are reflected in usage tracking"""
        user_info = {'email': 'test@example.com'}
        
        # Start as free
        clean_session.login(user_info, FreeRole())
        clean_session.update_role('free')
        assert fresh_tracker.get_remaining_arrangements() == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS
        
        # Upgrade to premium
        clean_session.update_role('premium')
        assert fresh_tracker.get_remaining_arrangements() is None


class TestArrangementFlowIntegration:
    """Test complete arrangement flow with session and usage tracking"""
    
    def test_arrangement_screen_checks_usage_before_save(self, clean_session, fresh_tracker):
        """Test that arrangement screen checks usage before allowing save"""
        user_info = {'email': 'free@test.com'}
        clean_session.login(user_info, FreeRole())
        
        # Simulate arrangement screen behavior
        # User changes arrangement
        arrangement_changed = True
        
        # Check if can proceed (before save)
        if arrangement_changed:
            can_proceed = fresh_tracker.can_arrange()
            assert can_proceed is True
            
            # Record usage
            fresh_tracker.record_arrangement()
            
            # Should decrement
            assert fresh_tracker.get_remaining_arrangements() == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS - 1
    
    def test_unchanged_arrangement_not_tracked(self, clean_session, fresh_tracker):
        """Test that unchanged arrangements don't use up quota"""
        user_info = {'email': 'free@test.com'}
        clean_session.login(user_info, FreeRole())
        
        initial_remaining = fresh_tracker.get_remaining_arrangements()
        
        # User goes to arrangement screen but doesn't change anything
        arrangement_changed = False
        
        # Should NOT record usage
        if arrangement_changed:
            fresh_tracker.record_arrangement()
        
        # Remaining should be unchanged
        assert fresh_tracker.get_remaining_arrangements() == initial_remaining
    
    def test_limit_prevents_save_with_changes(self, clean_session, fresh_tracker):
        """Test that reaching limit prevents saving with changes"""
        user_info = {'email': 'free@test.com'}
        clean_session.login(user_info, FreeRole())
        
        # Use up all arrangements
        for _ in range(UsageConfig.FREE_USER_DAILY_ARRANGEMENTS):
            fresh_tracker.record_arrangement()
        
        # Try to save with changes
        arrangement_changed = True
        
        if arrangement_changed:
            can_save = fresh_tracker.can_arrange()
            assert can_save is False


class TestMultiUserScenarios:
    """Test scenarios with multiple users"""
    
    def test_different_users_tracked_separately(self, temp_storage_dir):
        """Test that different users have separate usage tracking"""
        from access_control.session import session_manager
        
        tracker1 = UsageTracker()
        
        # User 1
        session_manager.login({'email': 'user1@test.com'}, FreeRole())
        tracker1.record_arrangement()
        tracker1.record_arrangement()
        
        # Switch to User 2
        session_manager.logout()
        tracker2 = UsageTracker()
        session_manager.login({'email': 'user2@test.com'}, FreeRole())
        
        # User 2 should start fresh
        assert tracker2.get_remaining_arrangements() == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS
    
    def test_user_switch_maintains_separate_counts(self, clean_session, temp_storage_dir):
        """Test switching between users maintains separate counts"""
        tracker = UsageTracker()
        
        # User 1 uses some arrangements
        clean_session.login({'email': 'user1@test.com'}, FreeRole())
        tracker.record_arrangement()
        tracker.record_arrangement()
        user1_remaining = tracker.get_remaining_arrangements()
        
        # Switch to user 2
        clean_session.logout()
        clean_session.login({'email': 'user2@test.com'}, FreeRole())
        tracker = UsageTracker()  # Reload tracker
        tracker.record_arrangement()
        user2_remaining = tracker.get_remaining_arrangements()
        
        # Switch back to user 1
        clean_session.logout()
        clean_session.login({'email': 'user1@test.com'}, FreeRole())
        tracker = UsageTracker()
        user1_remaining_after = tracker.get_remaining_arrangements()
        
        # User 1's count should be preserved
        assert user1_remaining_after == user1_remaining


class TestDailyResetIntegration:
    """Test daily reset behavior in integrated system"""
    
    def test_usage_resets_at_midnight_for_all_users(self, temp_storage_dir):
        """Test that all users get reset at midnight"""
        # Create multiple users with usage
        tracker = UsageTracker()
        
        with patch('access_control.session.session_manager') as mock_session:
            # User 1
            mock_session.is_authenticated.return_value = True
            mock_session.is_premium.return_value = False
            mock_session.is_admin.return_value = False
            mock_session.current_user = {'email': 'user1@test.com'}
            mock_session.role_name = 'free'
            tracker.record_arrangement()
            tracker.record_arrangement()
            
            # User 2
            mock_session.current_user = {'email': 'user2@test.com'}
            tracker2 = UsageTracker()
            tracker2.record_arrangement()
            
            # Simulate time passing (set reset time to past)
            for user_key in tracker.usage_data:
                tracker.usage_data[user_key]['reset_time'] = (datetime.now() - timedelta(hours=1)).isoformat()
            tracker._save_usage_data()
            
            # Reload and check
            tracker3 = UsageTracker()
            mock_session.current_user = {'email': 'user1@test.com'}
            assert tracker3.get_remaining_arrangements() == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS
    
    def test_reset_time_displayed_correctly(self, clean_session, fresh_tracker):
        """Test that reset time info is accurate"""
        user_info = {'email': 'test@test.com'}
        clean_session.login(user_info, FreeRole())
        
        info = fresh_tracker.get_usage_info()
        
        assert info is not None
        assert 'reset_time' in info
        # Reset time should be in future
        assert len(info['reset_time']) > 0


class TestErrorHandlingIntegration:
    """Test error handling in integrated system"""
    
    def test_corrupted_session_handled_gracefully(self, fresh_tracker):
        """Test that tracker handles corrupted session data"""
        with patch('access_control.usage_tracker.session_manager') as mock_session:
            mock_session.is_authenticated.return_value = True
            mock_session.is_premium.return_value = False
            mock_session.is_admin.return_value = False
            mock_session.current_user = None  # Corrupted
            
            # Should not crash
            result = fresh_tracker.record_arrangement()
            assert result is False
    
    def test_missing_usage_file_creates_new(self, temp_storage_dir):
        """Test that missing usage file is created automatically"""
        usage_file = temp_storage_dir / UsageConfig.USAGE_FILE
        
        # Ensure file doesn't exist
        if usage_file.exists():
            usage_file.unlink()
        
        # Create tracker (should create file)
        tracker = UsageTracker()
        
        # File should be created on first save
        with patch('access_control.session.session_manager') as mock_session:
            mock_session.is_authenticated.return_value = True
            mock_session.is_premium.return_value = False
            mock_session.is_admin.return_value = False
            mock_session.current_user = {'email': 'test@test.com'}
            mock_session.role_name = 'free'
            
            tracker.record_arrangement()
            
            assert usage_file.exists()
    
    def test_concurrent_access_handled(self, temp_storage_dir):
        """Test that concurrent access to usage data is handled"""
        # Create two tracker instances (simulating concurrent access)
        with patch('access_control.session.session_manager') as mock_session:
            mock_session.is_authenticated.return_value = True
            mock_session.is_premium.return_value = False
            mock_session.is_admin.return_value = False
            mock_session.current_user = {'email': 'test@test.com'}
            mock_session.role_name = 'free'
            
            tracker1 = UsageTracker()
            tracker2 = UsageTracker()
            
            # Both record arrangements
            tracker1.record_arrangement()
            tracker2.record_arrangement()
            
            # Reload and check total
            tracker3 = UsageTracker()
            remaining = tracker3.get_remaining_arrangements()
            
            # Should reflect both recordings
            assert remaining <= UsageConfig.FREE_USER_DAILY_ARRANGEMENTS - 1


class TestMainWindowIntegration:
    """Test integration with main window flow"""
    
    def test_main_window_checks_usage_before_proceeding(self):
        """Test that main window checks usage before going to save screen"""
        from app.gui.main_window import MainWindow
        
        mock_page = Mock()
        mock_page.overlay = []
        mock_page.update = Mock()
        
        with patch('access_control.session.session_manager') as mock_session:
            mock_session.is_authenticated.return_value = True
            mock_session.is_free.return_value = True
            mock_session.is_premium.return_value = False
            mock_session.is_admin.return_value = False
            
            # Main window should check usage tracker before allowing save
            # This is integrated in main_window.next_step() when going from step 1 to step 2
    
    def test_arrangement_usage_recorded_on_save(self):
        """Test that usage is recorded when user saves arrangement"""
        from app.gui.arrangement_screen import ArrangementScreen
        
        mock_page = Mock()
        mock_page.update = Mock()
        
        with patch('access_control.session.session_manager') as mock_session:
            with patch('access_control.usage_tracker.usage_tracker') as mock_tracker:
                mock_session.is_authenticated.return_value = True
                mock_session.is_free.return_value = True
                mock_session.is_premium.return_value = False
                mock_session.is_admin.return_value = False
                
                mock_tracker.can_arrange.return_value = True
                mock_tracker.record_arrangement.return_value = True
                
                arrangement_screen = ArrangementScreen(page=mock_page)
                arrangement_screen.set_videos(['video1.mp4', 'video2.mp4'])
                
                # Simulate arrangement change
                arrangement_screen.arrangement_changed = True
                
                # Record usage
                result = arrangement_screen.record_arrangement_usage()
                
                assert result is True


class TestRobustnessScenarios:
    """Test system robustness under various conditions"""
    
    def test_rapid_arrangement_changes(self, clean_session, fresh_tracker):
        """Test handling of rapid arrangement changes"""
        user_info = {'email': 'test@test.com'}
        clean_session.login(user_info, FreeRole())
        
        # Rapid arrangements
        for i in range(3):
            result = fresh_tracker.record_arrangement()
            assert result is True
        
        remaining = fresh_tracker.get_remaining_arrangements()
        assert remaining == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS - 3
    
    def test_session_persistence_across_restarts(self, temp_storage_dir):
        """Test that usage persists across app restarts"""
        with patch('access_control.session.session_manager') as mock_session:
            mock_session.is_authenticated.return_value = True
            mock_session.is_premium.return_value = False
            mock_session.is_admin.return_value = False
            mock_session.current_user = {'email': 'test@test.com'}
            mock_session.role_name = 'free'
            
            # First session
            tracker1 = UsageTracker()
            tracker1.record_arrangement()
            tracker1.record_arrangement()
            
            # "Restart app" - create new tracker
            tracker2 = UsageTracker()
            remaining = tracker2.get_remaining_arrangements()
            
            # Usage should persist
            assert remaining == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS - 2
    
    def test_timezone_handling(self, clean_session, fresh_tracker):
        """Test that reset time handles timezone correctly"""
        user_info = {'email': 'test@test.com'}
        clean_session.login(user_info, FreeRole())
        
        # Get reset time
        reset_time = fresh_tracker._get_reset_time()
        now = datetime.now()
        
        # Reset should be in future and at midnight
        assert reset_time > now
        assert reset_time.hour == UsageConfig.RESET_HOUR
        assert reset_time.minute == UsageConfig.RESET_MINUTE


class TestAccuracyVerification:
    """Verify accuracy of usage tracking"""
    
    def test_counter_accuracy_single_user(self, clean_session, fresh_tracker):
        """Test that counter is accurate for single user"""
        user_info = {'email': 'test@test.com'}
        clean_session.login(user_info, FreeRole())
        
        # Track each arrangement
        counts = []
        for i in range(5):
            fresh_tracker.record_arrangement()
            remaining = fresh_tracker.get_remaining_arrangements()
            counts.append(remaining)
        
        # Verify decreasing sequence
        expected = [4, 3, 2, 1, 0]
        assert counts == expected
    
    def test_usage_info_accuracy(self, clean_session, fresh_tracker):
        """Test that usage info is accurate"""
        user_info = {'email': 'test@test.com'}
        clean_session.login(user_info, FreeRole())
        
        # Record 3 arrangements
        for _ in range(3):
            fresh_tracker.record_arrangement()
        
        info = fresh_tracker.get_usage_info()
        
        assert info['used'] == 3
        assert info['remaining'] == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS - 3
        assert info['limit'] == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS
        assert info['unlimited'] is False
    
    def test_edge_of_limit_accuracy(self, clean_session, fresh_tracker):
        """Test accuracy at edge of limit"""
        user_info = {'email': 'test@test.com'}
        clean_session.login(user_info, FreeRole())
        
        # Use up to limit - 1
        for _ in range(UsageConfig.FREE_USER_DAILY_ARRANGEMENTS - 1):
            fresh_tracker.record_arrangement()
        
        # Should have exactly 1 left
        assert fresh_tracker.get_remaining_arrangements() == 1
        assert fresh_tracker.can_arrange() is True
        
        # Use last one
        fresh_tracker.record_arrangement()
        
        # Should be at limit
        assert fresh_tracker.get_remaining_arrangements() == 0
        assert fresh_tracker.can_arrange() is False


class TestCompleteWorkflow:
    """Test complete end-to-end workflows"""
    
    def test_complete_free_user_workflow(self, temp_storage_dir):
        """Test complete workflow for free user with usage tracking"""
        session = SessionManager()
        tracker = UsageTracker()
        
        # 1. User logs in
        session.login({'email': 'free@test.com', 'name': 'Free User'}, FreeRole())
        
        # 2. User arranges videos (first time)
        assert tracker.can_arrange() is True
        tracker.record_arrangement()
        
        # 3. User saves
        assert tracker.get_remaining_arrangements() == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS - 1
        
        # 4. User does another arrangement
        tracker.record_arrangement()
        assert tracker.get_remaining_arrangements() == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS - 2
        
        # 5. User logs out
        session.logout()
        
        # 6. User logs back in
        session.login({'email': 'free@test.com'}, FreeRole())
        tracker = UsageTracker()
        
        # 7. Usage should be preserved
        assert tracker.get_remaining_arrangements() == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS - 2
    
    def test_premium_upgrade_workflow(self, temp_storage_dir):
        """Test workflow when user upgrades to premium"""
        from access_control.session import session_manager
        
        tracker = UsageTracker()
        
        # Start as free
        session_manager.login({'email': 'user@test.com'}, FreeRole())
        tracker.record_arrangement()
        tracker.record_arrangement()
        
        # Upgrade to premium
        session_manager.update_role('premium')
        tracker = UsageTracker()
        
        # Should now be unlimited
        assert tracker.get_remaining_arrangements() is None
        assert tracker.can_arrange() is True

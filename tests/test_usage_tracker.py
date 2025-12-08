"""
Unit tests for usage tracker - daily arrangement limits for free users
Tests the UsageTracker class functionality
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from access_control.usage_tracker import UsageTracker, UsageConfig
from access_control.roles import FreeRole, PremiumRole, GuestRole, AdminRole


@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create temporary storage directory for tests"""
    storage_dir = tmp_path / "usage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    # Patch the storage directory
    original_dir = UsageConfig.STORAGE_DIR
    UsageConfig.STORAGE_DIR = storage_dir
    
    yield storage_dir
    
    # Restore original
    UsageConfig.STORAGE_DIR = original_dir


@pytest.fixture
def mock_session_manager():
    """Mock session manager for testing"""
    with patch('access_control.usage_tracker.session_manager') as mock:
        yield mock


@pytest.fixture
def usage_tracker(temp_storage_dir):
    """Create a fresh usage tracker instance"""
    return UsageTracker()


class TestUsageTrackerInitialization:
    """Test usage tracker initialization and setup"""
    
    def test_creates_storage_directory(self, temp_storage_dir):
        """Test that storage directory is created on init"""
        tracker = UsageTracker()
        assert temp_storage_dir.exists()
    
    def test_loads_empty_data_on_first_run(self, usage_tracker):
        """Test that usage_data is empty dict on first run"""
        assert usage_tracker.usage_data == {}
    
    def test_loads_existing_data(self, temp_storage_dir):
        """Test that existing data is loaded correctly"""
        # Create test data
        test_data = {
            "user@test.com": {
                "role": "free",
                "arrangements_today": 3,
                "reset_time": datetime.now().isoformat()
            }
        }
        
        # Write to file
        usage_file = temp_storage_dir / UsageConfig.USAGE_FILE
        with open(usage_file, 'w') as f:
            json.dump(test_data, f)
        
        # Create tracker and verify data loaded
        tracker = UsageTracker()
        assert tracker.usage_data == test_data


class TestUsageTrackerFreeUsers:
    """Test usage tracking for free users"""
    
    def test_free_user_can_arrange_initially(self, usage_tracker, mock_session_manager):
        """Test that free user can arrange when starting fresh"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.is_free.return_value = True
        mock_session_manager.current_user = {'email': 'free@test.com'}
        mock_session_manager.role_name = 'free'
        
        assert usage_tracker.can_arrange() is True
    
    def test_free_user_has_daily_limit(self, usage_tracker, mock_session_manager):
        """Test that free user has correct daily limit"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = {'email': 'free@test.com'}
        mock_session_manager.role_name = 'free'
        
        remaining = usage_tracker.get_remaining_arrangements()
        assert remaining == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS
    
    def test_free_user_arrangement_decrements_counter(self, usage_tracker, mock_session_manager):
        """Test that recording arrangement decrements counter"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = {'email': 'free@test.com'}
        mock_session_manager.role_name = 'free'
        
        initial = usage_tracker.get_remaining_arrangements()
        usage_tracker.record_arrangement()
        after = usage_tracker.get_remaining_arrangements()
        
        assert after == initial - 1
    
    def test_free_user_reaches_limit(self, usage_tracker, mock_session_manager):
        """Test that free user cannot arrange after reaching limit"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = {'email': 'free@test.com'}
        mock_session_manager.role_name = 'free'
        
        # Use up all arrangements
        for _ in range(UsageConfig.FREE_USER_DAILY_ARRANGEMENTS):
            assert usage_tracker.record_arrangement() is True
        
        # Should not be able to arrange anymore
        assert usage_tracker.can_arrange() is False
        assert usage_tracker.record_arrangement() is False
    
    def test_free_user_multiple_recordings(self, usage_tracker, mock_session_manager):
        """Test recording multiple arrangements"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = {'email': 'free@test.com'}
        mock_session_manager.role_name = 'free'
        
        # Record 3 arrangements
        for i in range(3):
            result = usage_tracker.record_arrangement()
            assert result is True
            remaining = usage_tracker.get_remaining_arrangements()
            assert remaining == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS - (i + 1)


class TestUsageTrackerPremiumUsers:
    """Test usage tracking for premium users"""
    
    def test_premium_user_unlimited_arrangements(self, usage_tracker, mock_session_manager):
        """Test that premium users have unlimited arrangements"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = True
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = {'email': 'premium@test.com'}
        
        remaining = usage_tracker.get_remaining_arrangements()
        assert remaining is None  # None = unlimited
    
    def test_premium_user_can_always_arrange(self, usage_tracker, mock_session_manager):
        """Test that premium users can always arrange"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = True
        mock_session_manager.is_admin.return_value = False
        
        assert usage_tracker.can_arrange() is True
    
    def test_premium_user_recording_not_tracked(self, usage_tracker, mock_session_manager):
        """Test that premium user arrangements are not tracked"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = True
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = {'email': 'premium@test.com'}
        
        # Record many arrangements
        for _ in range(100):
            assert usage_tracker.record_arrangement() is True
        
        # Should still have unlimited
        assert usage_tracker.get_remaining_arrangements() is None


class TestUsageTrackerAdminUsers:
    """Test usage tracking for admin users"""
    
    def test_admin_user_unlimited_arrangements(self, usage_tracker, mock_session_manager):
        """Test that admin users have unlimited arrangements"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = True
        mock_session_manager.current_user = {'email': 'admin@test.com'}
        
        remaining = usage_tracker.get_remaining_arrangements()
        assert remaining is None  # None = unlimited
    
    def test_admin_user_can_always_arrange(self, usage_tracker, mock_session_manager):
        """Test that admin users can always arrange"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = True
        
        assert usage_tracker.can_arrange() is True


class TestUsageTrackerGuestUsers:
    """Test usage tracking for guest users"""
    
    def test_guest_user_cannot_arrange(self, usage_tracker, mock_session_manager):
        """Test that guest users cannot arrange"""
        mock_session_manager.is_authenticated.return_value = False
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        
        assert usage_tracker.can_arrange() is False
    
    def test_guest_user_has_zero_arrangements(self, usage_tracker, mock_session_manager):
        """Test that guest users have 0 arrangements"""
        mock_session_manager.is_authenticated.return_value = False
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = None
        
        remaining = usage_tracker.get_remaining_arrangements()
        assert remaining == 0
    
    def test_guest_user_cannot_record(self, usage_tracker, mock_session_manager):
        """Test that guest users cannot record arrangements"""
        mock_session_manager.is_authenticated.return_value = False
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = None
        
        result = usage_tracker.record_arrangement()
        assert result is False


class TestUsageTrackerDailyReset:
    """Test daily reset functionality"""
    
    def test_reset_time_calculation(self, usage_tracker):
        """Test that reset time is calculated correctly (next midnight)"""
        reset_time = usage_tracker._get_reset_time()
        now = datetime.now()
        
        # Reset should be at midnight
        assert reset_time.hour == UsageConfig.RESET_HOUR
        assert reset_time.minute == UsageConfig.RESET_MINUTE
        
        # Reset should be in the future
        assert reset_time > now
    
    def test_usage_resets_after_midnight(self, usage_tracker, mock_session_manager):
        """Test that usage resets after reset time passes"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = {'email': 'free@test.com'}
        mock_session_manager.role_name = 'free'
        
        # Record some arrangements
        usage_tracker.record_arrangement()
        usage_tracker.record_arrangement()
        
        # Manually set reset time to past
        user_key = 'free@test.com'
        usage_tracker.usage_data[user_key]['reset_time'] = (datetime.now() - timedelta(hours=1)).isoformat()
        usage_tracker._save_usage_data()
        
        # Check if reset occurs
        usage_tracker._check_and_reset_if_needed(user_key)
        
        # Should be reset to 0
        assert usage_tracker.usage_data[user_key]['arrangements_today'] == 0
    
    def test_reset_does_not_trigger_before_time(self, usage_tracker, mock_session_manager):
        """Test that reset doesn't trigger before reset time"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = {'email': 'free@test.com'}
        mock_session_manager.role_name = 'free'
        
        # Record some arrangements
        usage_tracker.record_arrangement()
        usage_tracker.record_arrangement()
        
        user_key = 'free@test.com'
        before = usage_tracker.usage_data[user_key]['arrangements_today']
        
        # Reset time is in future, so no reset should occur
        usage_tracker._check_and_reset_if_needed(user_key)
        
        after = usage_tracker.usage_data[user_key]['arrangements_today']
        assert after == before


class TestUsageTrackerPersistence:
    """Test data persistence"""
    
    def test_data_persists_between_instances(self, temp_storage_dir, mock_session_manager):
        """Test that usage data persists between tracker instances"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = {'email': 'free@test.com'}
        mock_session_manager.role_name = 'free'
        
        # Create first tracker and record arrangements
        tracker1 = UsageTracker()
        tracker1.record_arrangement()
        tracker1.record_arrangement()
        remaining1 = tracker1.get_remaining_arrangements()
        
        # Create new tracker instance
        tracker2 = UsageTracker()
        remaining2 = tracker2.get_remaining_arrangements()
        
        # Should have same remaining count
        assert remaining1 == remaining2
    
    def test_save_and_load_cycle(self, usage_tracker, mock_session_manager):
        """Test that data survives save/load cycle"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = {'email': 'free@test.com'}
        mock_session_manager.role_name = 'free'
        
        # Record arrangements
        usage_tracker.record_arrangement()
        usage_tracker.record_arrangement()
        usage_tracker.record_arrangement()
        
        # Save
        usage_tracker._save_usage_data()
        
        # Load
        loaded_data = usage_tracker._load_usage_data()
        
        # Verify
        assert 'free@test.com' in loaded_data
        assert loaded_data['free@test.com']['arrangements_today'] == 3


class TestUsageTrackerGetUsageInfo:
    """Test get_usage_info method"""
    
    def test_free_user_usage_info(self, usage_tracker, mock_session_manager):
        """Test usage info for free user"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = {'email': 'free@test.com'}
        mock_session_manager.role_name = 'free'
        
        # Record 2 arrangements
        usage_tracker.record_arrangement()
        usage_tracker.record_arrangement()
        
        info = usage_tracker.get_usage_info()
        
        assert info is not None
        assert info['unlimited'] is False
        assert info['used'] == 2
        assert info['limit'] == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS
        assert info['remaining'] == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS - 2
        assert 'reset_time' in info
    
    def test_premium_user_usage_info(self, usage_tracker, mock_session_manager):
        """Test usage info for premium user"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = True
        mock_session_manager.is_admin.return_value = False
        
        info = usage_tracker.get_usage_info()
        
        assert info is not None
        assert info['unlimited'] is True
    
    def test_guest_user_usage_info(self, usage_tracker, mock_session_manager):
        """Test usage info for guest user"""
        mock_session_manager.is_authenticated.return_value = False
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = None
        
        info = usage_tracker.get_usage_info()
        
        assert info is not None
        assert info['unlimited'] is False
        assert info['used'] == 0
        assert info['limit'] == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS
        assert info['remaining'] == 0


class TestUsageTrackerEdgeCases:
    """Test edge cases and error handling"""
    
    def test_handles_missing_user_key(self, usage_tracker, mock_session_manager):
        """Test handling when user key cannot be determined"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = None  # No user data
        
        result = usage_tracker.record_arrangement()
        assert result is False
    
    def test_handles_corrupted_usage_file(self, temp_storage_dir):
        """Test handling of corrupted usage file"""
        # Write corrupted data
        usage_file = temp_storage_dir / UsageConfig.USAGE_FILE
        with open(usage_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Should not crash, should return empty dict
        tracker = UsageTracker()
        assert tracker.usage_data == {}
    
    def test_user_key_from_email(self, usage_tracker, mock_session_manager):
        """Test that user key is extracted from email"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.current_user = {'email': 'test@example.com'}
        
        user_key = usage_tracker._get_user_key()
        assert user_key == 'test@example.com'
    
    def test_user_key_from_uid(self, usage_tracker, mock_session_manager):
        """Test that user key falls back to uid if no email"""
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.current_user = {'uid': 'user123'}
        
        user_key = usage_tracker._get_user_key()
        assert user_key == 'user123'
    
    def test_different_users_tracked_separately(self, usage_tracker, mock_session_manager):
        """Test that different users are tracked separately"""
        # User 1
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.is_premium.return_value = False
        mock_session_manager.is_admin.return_value = False
        mock_session_manager.current_user = {'email': 'user1@test.com'}
        mock_session_manager.role_name = 'free'
        
        usage_tracker.record_arrangement()
        usage_tracker.record_arrangement()
        
        # User 2
        mock_session_manager.current_user = {'email': 'user2@test.com'}
        
        remaining = usage_tracker.get_remaining_arrangements()
        
        # User 2 should start fresh
        assert remaining == UsageConfig.FREE_USER_DAILY_ARRANGEMENTS

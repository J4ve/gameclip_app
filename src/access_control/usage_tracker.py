"""
Usage Tracker - Track daily arrangement limits for users
Manages daily usage counts and automatic resets for free users
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from .session import session_manager
from .roles import RoleType


class UsageConfig:
    """Configuration for usage limits"""
    FREE_USER_DAILY_ARRANGEMENTS = 5  # Free users can arrange 5 times per day
    STORAGE_DIR = Path("storage/data/usage")
    USAGE_FILE = "usage_tracking.json"
    
    # Time when daily limit resets (midnight)
    RESET_HOUR = 0
    RESET_MINUTE = 0


class UsageTracker:
    """
    Tracks daily arrangement usage for users
    
    Features:
    - Tracks arrangement count per user per day
    - Automatic daily reset at midnight
    - Verifies user role before tracking
    - Persistent storage in JSON file
    """
    
    def __init__(self):
        self.storage_path = UsageConfig.STORAGE_DIR / UsageConfig.USAGE_FILE
        self._ensure_storage_dir()
        self.usage_data = self._load_usage_data()
    
    def _ensure_storage_dir(self):
        """Create storage directory if it doesn't exist"""
        UsageConfig.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_usage_data(self) -> Dict:
        """Load usage data from file"""
        if not self.storage_path.exists():
            return {}
        
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading usage data: {e}")
            return {}
    
    def _save_usage_data(self):
        """Save usage data to file"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            print(f"Error saving usage data: {e}")
    
    def _get_user_key(self) -> Optional[str]:
        """Get unique key for current user"""
        if not session_manager.is_authenticated():
            return None
        
        user_data = session_manager.current_user
        if not user_data:
            return None
        
        # Use email or user_id as unique identifier
        return user_data.get('email') or user_data.get('uid') or user_data.get('user_id')
    
    def _get_reset_time(self) -> datetime:
        """Calculate next reset time (midnight)"""
        now = datetime.now()
        next_reset = now.replace(
            hour=UsageConfig.RESET_HOUR,
            minute=UsageConfig.RESET_MINUTE,
            second=0,
            microsecond=0
        )
        
        # If we're past today's reset time, move to tomorrow
        if now >= next_reset:
            next_reset += timedelta(days=1)
        
        return next_reset
    
    def _check_and_reset_if_needed(self, user_key: str):
        """Check if reset time has passed and reset usage if needed"""
        if user_key not in self.usage_data:
            return
        
        user_data = self.usage_data[user_key]
        reset_time_str = user_data.get('reset_time')
        
        if not reset_time_str:
            # No reset time set, initialize it
            user_data['reset_time'] = self._get_reset_time().isoformat()
            user_data['arrangements_today'] = 0
            self._save_usage_data()
            return
        
        reset_time = datetime.fromisoformat(reset_time_str)
        now = datetime.now()
        
        # If we've passed the reset time, reset the counter
        if now >= reset_time:
            user_data['arrangements_today'] = 0
            user_data['reset_time'] = self._get_reset_time().isoformat()
            user_data['last_reset'] = now.isoformat()
            self._save_usage_data()
            print(f"Daily usage reset for user {user_key}")
    
    def get_remaining_arrangements(self) -> Optional[int]:
        """
        Get remaining arrangements for current user
        
        Returns:
            int: Remaining arrangements for free users
            None: Unlimited (guest, premium, admin)
        """
        # Premium and admin have unlimited
        if session_manager.is_premium() or session_manager.is_admin():
            return None  # Unlimited
        
        # Guests can't arrange at all
        if not session_manager.is_authenticated():
            return 0
        
        # Free users have daily limit
        user_key = self._get_user_key()
        if not user_key:
            return 0
        
        # Check if reset is needed
        self._check_and_reset_if_needed(user_key)
        
        # Get or initialize user data
        if user_key not in self.usage_data:
            self.usage_data[user_key] = {
                'role': session_manager.role_name,
                'arrangements_today': 0,
                'reset_time': self._get_reset_time().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            self._save_usage_data()
        
        user_data = self.usage_data[user_key]
        used = user_data.get('arrangements_today', 0)
        
        return max(0, UsageConfig.FREE_USER_DAILY_ARRANGEMENTS - used)
    
    def can_arrange(self) -> bool:
        """
        Check if current user can arrange videos
        
        Returns:
            bool: True if user can arrange, False otherwise
        """
        remaining = self.get_remaining_arrangements()
        
        # None means unlimited
        if remaining is None:
            return True
        
        return remaining > 0
    
    def record_arrangement(self) -> bool:
        """
        Record an arrangement usage
        
        Returns:
            bool: True if recorded successfully, False if limit reached
        """
        # Premium and admin don't count
        if session_manager.is_premium() or session_manager.is_admin():
            return True
        
        # Guests can't arrange
        if not session_manager.is_authenticated():
            return False
        
        # Check if user can still arrange
        if not self.can_arrange():
            return False
        
        user_key = self._get_user_key()
        if not user_key:
            return False
        
        # Check if reset is needed
        self._check_and_reset_if_needed(user_key)
        
        # Increment counter
        if user_key not in self.usage_data:
            self.usage_data[user_key] = {
                'role': session_manager.role_name,
                'arrangements_today': 0,
                'reset_time': self._get_reset_time().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
        
        self.usage_data[user_key]['arrangements_today'] += 1
        self.usage_data[user_key]['last_updated'] = datetime.now().isoformat()
        self.usage_data[user_key]['role'] = session_manager.role_name  # Update role in case it changed
        
        self._save_usage_data()
        
        remaining = self.get_remaining_arrangements()
        print(f"Arrangement recorded. Remaining today: {remaining}")
        
        return True
    
    def get_reset_time_str(self) -> str:
        """Get formatted string of when the limit resets"""
        user_key = self._get_user_key()
        
        if not user_key or user_key not in self.usage_data:
            reset_time = self._get_reset_time()
        else:
            reset_time_str = self.usage_data[user_key].get('reset_time')
            if reset_time_str:
                reset_time = datetime.fromisoformat(reset_time_str)
            else:
                reset_time = self._get_reset_time()
        
        now = datetime.now()
        time_diff = reset_time - now
        
        hours = int(time_diff.total_seconds() // 3600)
        minutes = int((time_diff.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def get_usage_info(self) -> Dict:
        """
        Get detailed usage information for current user
        
        Returns:
            dict: Usage information including remaining, used, reset time
        """
        remaining = self.get_remaining_arrangements()
        
        if remaining is None:
            return {
                'unlimited': True,
                'remaining': None,
                'used': 0,
                'limit': None,
                'reset_time': None
            }
        
        user_key = self._get_user_key()
        used = 0
        
        if user_key and user_key in self.usage_data:
            used = self.usage_data[user_key].get('arrangements_today', 0)
        
        return {
            'unlimited': False,
            'remaining': remaining,
            'used': used,
            'limit': UsageConfig.FREE_USER_DAILY_ARRANGEMENTS,
            'reset_time': self.get_reset_time_str()
        }


# Global usage tracker instance
usage_tracker = UsageTracker()

# Export
__all__ = ['UsageTracker', 'UsageConfig', 'usage_tracker']

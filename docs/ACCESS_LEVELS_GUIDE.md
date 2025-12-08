# Access Levels Implementation Guide

## Overview
This document describes the access level system that controls what users can do based on their authentication status and role.

## Access Levels

### 🚫 Guest (Not Authenticated)
**What they CAN do:**
- Select videos (step 1)
- View the arrangement screen (but all controls are locked)
- Continue directly to merge with original order
- Remove videos from selection

**What they CANNOT do:**
- Rearrange videos (move up/down)
- Sort videos
- Duplicate videos
- Lock video positions
- Change the order in any way

**UI Experience:**
- When they reach the arrangement screen, they see a lockout overlay with:
  - Lock icon and "Arrangement Locked" message
  - Explanation that login is required for arrangement features
  - Two buttons:
    - "Login to Arrange" - goes back to selection screen to login
    - "Continue to Merge" - proceeds to merge with original order
- All arrangement buttons (move up/down, duplicate) are disabled and greyed out

---

### 🆓 Free User (Authenticated)
**What they CAN do:**
- Everything guests can do, PLUS:
- Rearrange videos (move up/down)
- Sort videos by name, date, size
- Duplicate videos
- **Daily limit: 10 arrangements per day**

**What they CANNOT do:**
- Lock video positions (premium feature)
- Unlimited arrangements

**Daily Limit System:**
- Free users get **10 arrangements per day**
- An "arrangement" is counted ONLY when:
  - User actually changes the video order (detected automatically)
  - The change is different from the original order from selection screen
- If user enters arrangement screen but doesn't change anything = **NO usage counted**
- Limit resets at midnight (00:00) every day

**UI Experience:**
- See usage counter in header: "Arrangements: 3/10 (resets in 4h 23m)"
- Orange indicator appears when order is modified: "🟠 Arrangement modified"
- Usage count updates in real-time when arrangement is saved
- Counter color changes:
  - Blue when arrangements remaining
  - Red when limit reached
- All arrangement controls fully enabled
- Duplicate toggle visible and functional

---

### 💎 Premium User (Paid)
**What they CAN do:**
- Everything free users can do, PLUS:
- **Unlimited arrangements** (no daily limit)
- Lock video positions (premium feature)
- No ads

**UI Experience:**
- No usage counter (unlimited)
- No change indicator (not needed)
- Lock/unlock buttons visible next to each video
- Gold lock indicator for locked videos
- Premium badge in header: "🔒 Lock enabled"

---

### 👑 Admin
**What they CAN do:**
- Everything premium users can do, PLUS:
- Access to admin dashboard
- User management
- Analytics and audit logs

---

## Technical Implementation

### Files Modified

1. **`src/access_control/usage_tracker.py`** (NEW)
   - Tracks daily arrangement usage for free users
   - Stores data in `storage/data/usage/usage_tracking.json`
   - Automatically resets at midnight
   - Methods:
     - `can_arrange()` - Check if user can still arrange
     - `record_arrangement()` - Record a usage when order changes
     - `get_remaining_arrangements()` - Get remaining count
     - `get_usage_info()` - Get detailed usage information
     - `get_reset_time_str()` - Get formatted reset time

2. **`src/app/gui/arrangement_screen.py`**
   - Added guest lockout overlay
   - Added usage tracking and change detection
   - Disabled all controls for guests
   - Shows usage counter for free users
   - Shows change indicator when order is modified
   - Methods:
     - `_check_arrangement_changed()` - Compares current vs original order
     - `_update_change_indicator()` - Updates UI and records usage if needed
     - `_go_back_to_login()` - Navigates back to login

3. **`src/app/gui/selection_screen.py`**
   - Added `original_order` property to track initial selection order

4. **`src/app/gui/main_window.py`**
   - Saves original order when navigating to arrangement screen

### Change Detection Logic

The system automatically detects when the user changes the arrangement:

1. When user moves to arrangement screen, `original_order` is saved
2. Every time an arrangement action occurs (move, sort, duplicate, remove):
   - `_update_change_indicator()` is called
   - Compares current `self.videos` with `self.original_order`
   - If different and free user and not already recorded:
     - Calls `usage_tracker.record_arrangement()`
     - Updates usage counter display
     - Shows "Arrangement modified" indicator

3. Actions that trigger change detection:
   - Moving video up/down
   - Sorting by any criteria
   - Duplicating a video
   - Removing a video
   - Toggling allow duplicates (if it removes duplicates)

### Usage Tracking Data

Stored in: `storage/data/usage/usage_tracking.json`

Format:
```json
{
  "user@example.com": {
    "role": "free",
    "arrangements_today": 3,
    "reset_time": "2025-12-10T00:00:00",
    "last_updated": "2025-12-09T15:30:45",
    "last_reset": "2025-12-09T00:00:00"
  }
}
```

### Configuration

In `usage_tracker.py`:
```python
class UsageConfig:
    FREE_USER_DAILY_ARRANGEMENTS = 10  # Change this to adjust limit
    RESET_HOUR = 0  # Midnight
    RESET_MINUTE = 0
```

---

## User Journey Examples

### Guest User Journey
1. Guest selects 5 videos
2. Clicks "Next" → Goes to arrangement screen
3. Sees lockout overlay with locked arrangement controls
4. Can either:
   - Click "Login to Arrange" → goes back to login
   - Click "Continue to Merge" → proceeds with original order

### Free User Journey (First Arrangement)
1. Free user logs in and selects 5 videos
2. Clicks "Next" → Goes to arrangement screen
3. Sees: "Arrangements: 0/10 (resets in 8h 30m)"
4. Moves video #3 to position #1
5. Orange indicator appears: "🟠 Arrangement modified"
6. Counter updates: "Arrangements: 1/10 (resets in 8h 30m)"
7. Continues to merge

### Free User Journey (No Changes)
1. Free user selects videos and goes to arrangement
2. Just previews videos without moving anything
3. No indicator appears, no usage counted
4. Counter stays: "Arrangements: 1/10"
5. Can continue to merge without using a slot

### Free User at Limit
1. User has made 10 arrangements today
2. Selects new videos and goes to arrangement
3. Sees: "Arrangements: 10/10 (resets in 2h 15m)" in RED
4. Can still access screen but arrangement operations may be restricted
5. Must wait for midnight reset

---

## Testing Checklist

- [ ] Guest sees lockout overlay in arrangement screen
- [ ] Guest cannot move, sort, or duplicate videos
- [ ] Guest can click "Login to Arrange" to go back
- [ ] Guest can click "Continue to Merge" to proceed
- [ ] Free user sees usage counter
- [ ] Free user counter updates when arrangement changes
- [ ] Free user counter does NOT update when no changes made
- [ ] Orange "modified" indicator appears on arrangement change
- [ ] Usage resets at midnight
- [ ] Premium users see no usage counter (unlimited)
- [ ] Premium users can lock positions
- [ ] Admin users have all features

---

## Future Enhancements

Potential improvements:
1. Add "arrangement preview" mode for guests (read-only drag preview)
2. Show "X arrangements remaining" warning when approaching limit
3. Add option to purchase more arrangements for free users
4. Track different types of arrangements separately (moves vs duplicates)
5. Add analytics dashboard showing usage patterns

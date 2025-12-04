# Authentication System

## Overview
The Video Merger App now includes a role-based authentication system that appears before the main 3-step workflow. Users can login as guest or with Google authentication.

## Login Options

### Guest Login
- No registration required
- Limited to 5 merges per day
- Videos include watermark
- Ads enabled
- Cannot upload to YouTube
- Max video length: 10 minutes
- Max file size: 100MB

### Google Login (Mock Authentication)
Test accounts for development:
- **admin@test.com** / **admin123** (Admin role)
- **user@test.com** / **user123** (Normal role)  
- **premium@test.com** / **premium123** (Premium role)

You can also create new accounts with any email/password combination.

## Role Features

### Guest
- Save videos with watermark
- Merge up to 5 videos per day
- Ads displayed

### Normal User
- Upload to YouTube
- No watermark
- Up to 20 merges per day
- 30 minute video limit
- Ads displayed

### Premium User
- All features
- No ads
- No watermark  
- Unlimited merges
- No time/size limits

### Admin
- All premium features
- User management capabilities
- Debug tools and logs

## Technical Implementation

### Files Created/Modified
- `src/access_control/roles.py` - OOP role system with permissions
- `src/access_control/session.py` - Session management 
- `src/access_control/gui/auth_screen.py` - Login screen UI
- `src/access_control/auth/firebase_auth_mock.py` - Mock authentication
- `src/main.py` - Updated to show login screen first
- `src/app/gui/main_window.py` - Added user info and logout
- `src/app/gui/save_upload_screen.py` - Role-based restrictions and ads

### Role System (OOP)
The `roles.py` module defines:
- `Role` base class with permissions and limits
- `RoleManager` for creating and managing roles
- `Permission` enum for all available permissions
- `RoleLimits` dataclass for role restrictions

### Session Management
The global `session_manager` tracks:
- Current user info and role
- Permission checking methods
- Role-based feature toggles

## Usage

1. Start the app - login screen appears
2. Choose guest login or Google login
3. Proceed to the 3-step workflow with role-based features
4. Logout button available in top-right corner

## Development Notes

Currently uses mock authentication for development. For production:
1. Set up Firebase project
2. Enable Authentication and Firestore
3. Replace mock auth with real Firebase implementation
4. Configure `firebase_config.json`

The system is designed to be easily switched from mock to real Firebase authentication.
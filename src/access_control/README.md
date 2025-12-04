# Access Control (Python/Firebase Integration)

This folder contains Python modules for Firebase-based user access control, integrated with the existing Flet GUI.

## Structure

- `auth/` - Python Firebase authentication and role management
- `gui/` - Flet UI components for login, role-based features
- `config/` - Firebase configuration and examples
- `security/` - Firebase security rules

## Roles

- **guest** - Not logged in; can save videos with watermark/ads
- **normal** - Logged in; can upload & save, but has ads
- **premium** - No ads, full features
- **dev** - Access to logs and debug tools
- **admin** - User management (promote/demote roles)

## Setup

See README files in subdirectories for detailed setup instructions.

# Integrating Firebase Auth with Your Flet App

## Quick Start

1. Install dependencies:
   ```bash
   pip install firebase-admin pyrebase4
   ```

2. Set up Firebase (see `../auth/README.md` and `../config/README.md`)

3. In your main Flet app (`src/main.py`), import and use:

```python
from access_control.auth.firebase_auth import firebase_auth
from access_control.auth.user_session import user_session
from access_control.gui.login_screen import LoginScreen
from access_control.gui.role_ui import AdBanner, AdminPanel

# In your main function:
def main(page: ft.Page):
    if not user_session.is_logged_in:
        # Show login screen
        login = LoginScreen(page, on_login_success=handle_login)
        page.add(login.build())
    else:
        # Show main app with role-based features
        page.add(
            AdBanner(),  # Shown for guest/normal only
            AdminPanel(),  # Shown for admin only
            # ... your app content
        )
```

## Example

See `example_integration.py` for a complete working example.

## Role-Based Components

- `AdBanner()` - Shows ads for guest/normal, hidden for premium+
- `AdminPanel()` - Admin-only user management panel
- `DevLogsPanel()` - Developer logs (dev/admin only)
- `RoleBasedContainer()` - Generic container with role requirements

## Checking Roles in Code

```python
from access_control.auth.user_session import user_session

if user_session.is_premium():
    # No ads, full features
    pass

if user_session.is_admin():
    # Admin-only code
    pass

if user_session.has_role('dev', 'admin'):
    # Dev or admin only
    pass
```

## Integration Steps

1. Replace your main window's user menu with login/logout buttons
2. Add `AdBanner()` to screens where you want ads
3. Add `AdminPanel()` to a settings/admin screen
4. Wrap premium features in `RoleBasedContainer(required_roles=['premium'])`
5. Check roles before allowing uploads, merges, etc.

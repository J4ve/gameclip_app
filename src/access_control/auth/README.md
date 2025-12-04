# Firebase Authentication for Python/Flet App

## Setup

1. Install Firebase dependencies:
   ```bash
   pip install firebase-admin pyrebase4
   ```

2. Get Firebase credentials:
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select your project (or create one)
   - Go to Project Settings → Service Accounts
   - Click "Generate new private key"
   - Save the JSON file as `serviceAccountKey.json` in this directory
   - **DO NOT commit this file to Git!**

3. Enable Firebase Authentication:
   - In Firebase Console, go to Authentication → Sign-in method
   - Enable Google provider
   - Add your authorized domains

4. Set up environment variable (optional):
   ```bash
   export FIREBASE_SERVICE_ACCOUNT=/path/to/serviceAccountKey.json
   ```

## Usage

### In your Flet app:

```python
from access_control.auth.firebase_auth import firebase_auth
from access_control.auth.user_session import user_session

# After user logs in with Google/Firebase (client-side):
# You'll get an ID token from the client

# Verify token and get user info
user_info = firebase_auth.verify_token(id_token)
if user_info:
    user_session.login(user_info, id_token)

# Check user role
if user_session.is_premium():
    # No ads
    pass

if user_session.is_admin():
    # Show admin panel
    pass

# Set role (admin only)
if user_session.is_admin():
    firebase_auth.set_user_role(uid='some-user-id', role='premium')
```

## Client-Side Login (Flet)

For Google/Firebase login in Flet, you'll need to:
1. Use `pyrebase4` or Firebase REST API for client-side auth
2. Get ID token after login
3. Pass token to `firebase_auth.verify_token()` to verify and extract role

See `../gui/login_screen.py` for a complete example.

## Roles

- **guest** - Not logged in (default)
- **normal** - Logged in, can upload, has ads
- **premium** - No ads, full features
- **dev** - Access to logs and debug tools
- **admin** - User management (promote/demote roles)

## Token Refresh

After changing a user's role with `set_user_role()`, the client must refresh their ID token:
```python
# Client must re-authenticate or call getIdToken(forceRefresh=True)
```

The new role will be in the refreshed token's custom claims.

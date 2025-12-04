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

## Firebase Access Control Integration

This module enables secure, role-based user management for your Flet desktop app using Firebase Authentication and Firestore. It supports login, registration, session management, and role-based feature access.

### Features
- Email/password authentication (Firebase)
- Role assignment: guest, normal, premium, dev, admin
- Session management and custom claims
- Firestore security rules for data protection
- Flet UI screens for login, registration, and role-based access

### Quick Start

1. **Create a Firebase Project**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project and enable Authentication (Email/Password)
   - Create a Firestore database (production mode recommended)

2. **Download Firebase Config**
   - In Project Settings > General, download your `firebase_config.json` and place it in `src/access_control/config/` (never commit secrets; use `.gitignore`)
   - Use the provided `firebase_config.json.example` as a template

3. **Install Python Dependencies**
   - In your virtual environment, run:
     ```bash
     pip install pyrebase4 firebase-admin flet
     ```

4. **Configure Firestore Security Rules**
   - Copy `security/firestore.rules` to your Firebase project (Firestore > Rules)
   - Adjust rules for your app's needs

5. **Integrate with Flet App**
   - See `gui/example_integration.py` for how to add login and role-based UI to your Flet app
   - Use `auth/firebase_auth.py` for authentication logic
   - Use `auth/user_session.py` for session and role management

### Usage Example
```python
from access_control.auth.firebase_auth import FirebaseAuth
from access_control.auth.user_session import UserSession
from access_control.gui.login_screen import LoginScreen

# Initialize Firebase
firebase_auth = FirebaseAuth(config_path='config/firebase_config.json')

# Create login screen
login_screen = LoginScreen(firebase_auth)

# After login, get user session and role
session = UserSession(firebase_auth)
role = session.get_role()

if role == 'admin':
    # Show admin features
    pass
```

### Security Notes
- **Never commit secrets**: Always use `.gitignore` for config files containing credentials.
- **Custom claims**: Roles are managed via Firebase custom claims and Firestore documents.
- **Session management**: User sessions are handled securely in Python; tokens are refreshed as needed.

### More Information
- See subdirectory README files for advanced setup, UI customization, and security rule details.
- For troubleshooting, see the main project README and Firebase documentation.

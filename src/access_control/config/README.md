# Firebase Configuration

## Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to Project Settings → General → Your apps
4. If you don't have a web app, click "Add app" → Web
5. Copy the Firebase config object
6. Create `firebase_config.json` in this directory (copy from `firebase_config.json.example`)
7. Paste your config values

## Files

- `firebase_config.json.example` - Template (commit this)
- `firebase_config.json` - Your actual config (DO NOT commit this)

## Usage in Python

```python
import json

with open('access_control/config/firebase_config.json') as f:
    config = json.load(f)

# Use with pyrebase
import pyrebase
firebase = pyrebase.initialize_app(config)
```

## .gitignore

Make sure these are in your `.gitignore`:
```
firebase_config.json
serviceAccountKey.json
.user_session
```

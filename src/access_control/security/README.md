# Firebase Configuration

## Files

- `firestore.rules` - Firestore database security rules (role-based access)
- `storage.rules` - Firebase Storage security rules (for video uploads)
- `firebase_config.json.example` - Example Firebase web app config

## Deploying Rules

1. Install Firebase CLI:
   ```bash
   npm install -g firebase-tools
   ```

2. Login to Firebase:
   ```bash
   firebase login
   ```

3. Initialize Firebase in your project:
   ```bash
   firebase init
   ```
   Select Firestore and Storage.

4. Copy rules to Firebase project:
   ```bash
   cp firestore.rules ../../firebase/firestore.rules
   ```

5. Deploy rules:
   ```bash
   firebase deploy --only firestore:rules
   firebase deploy --only storage:rules
   ```

## Security Notes

- Custom claims (roles) are set server-side only (via Firebase Admin SDK).
- Clients cannot modify their own roles—rules enforce this.
- `isAdmin()`, `isDev()`, `isPremium()` helpers check `request.auth.token.role`.
- After changing a role, client must refresh ID token to see new claims.

## Testing Rules

Use Firebase Emulator Suite for local testing:
```bash
firebase emulators:start
```

Or test in Firebase Console → Firestore → Rules → Playground.

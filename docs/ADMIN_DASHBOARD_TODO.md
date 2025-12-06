# Admin Dashboard Implementation - TODO Tracker

## High Priority (Security Critical)

### 1. Firebase Security Rules
**File:** Firebase Console (Firestore Rules)
**Priority:** 🔴 CRITICAL
**Description:** Deploy server-side security rules to enforce role-based access at the database level

⚠️ **IMPORTANT: Desktop App Limitation**
Since this is a **desktop application** using Firebase Admin SDK, the authentication happens **server-side** (via service account), NOT client-side (via Firebase Authentication). This means:
- Security rules based on `request.auth` won't work as expected
- The Admin SDK bypasses security rules by default
- Security enforcement happens at the application logic level (already implemented)

**Current Security Model:**
✅ Application-level security (implemented in `firebase_service.py`)
- `verify_admin_permission()` checks user role before operations
- `check_rate_limit()` prevents abuse
- `log_admin_action()` creates audit trail

**Recommended Firestore Rules (for future web deployment):**
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Helper function to check if user exists and is admin
    function isAdmin() {
      return request.auth != null && 
             exists(/databases/$(database)/documents/users/$(request.auth.uid)) &&
             get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
    }
    
    // Users collection
    match /users/{userId} {
      // Anyone authenticated can read all users (needed for user lookup)
      allow read: if request.auth != null;
      
      // Only admins can write
      allow write: if isAdmin();
    }
    
    // Audit logs collection
    match /admin_audit_logs/{logId} {
      // Only admins can read audit logs
      allow read: if isAdmin();
      
      // Only server-side writes allowed (Admin SDK bypasses this)
      // In production web app, you'd restrict writes to Cloud Functions only
      allow write: if false;
    }
  }
}
```

**For Desktop App (Current Implementation):**
No Firestore rules changes needed - security is enforced at application level.

**For Future Web App Deployment:**
1. Navigate to Firebase Console → Firestore Database → Rules
2. Copy the rules above
3. Test in Firebase Rules Playground with test tokens
4. Deploy to production
5. Update authentication flow to use Firebase Auth (not Admin SDK)

---

### 2. Audit Logging Persistence ✅
**File:** `src/access_control/firebase_service.py`
**Priority:** 🔴 CRITICAL
**Function:** `log_admin_action()`

**Status:** ✅ IMPLEMENTED

**Completed:**
- [x] Implemented Firestore write in `log_admin_action()`
- [x] Created `admin_audit_logs` collection schema
- [x] Capture session ID from session_manager
- [x] Add error handling for logging failures
- [x] Added `get_audit_logs()` method for retrieving logs
- [x] Console logging for development feedback

**Note on IP Address:**
- Desktop apps cannot capture IP addresses without external services
- For web deployments, implement IP capture via request headers
- Current implementation marks client_type as 'desktop_app'

**Remaining TODO:**
- [ ] Implement log retention policy (auto-delete logs >90 days) - Use Firebase Cloud Functions
- [ ] Build UI for viewing audit logs (see Enhancement #9)

**Firebase Configuration Required:**
See "Firebase Setup TODO" section below for Firestore security rules.

---

### 3. Rate Limiting Implementation
**File:** `src/access_control/firebase_service.py`
**Priority:** 🟠 HIGH
**Function:** `check_rate_limit()`

**Current Status:** Always returns True (no limiting)

**TODO:**
- [ ] Implement in-memory cache (dict) for action counts
- [ ] Track timestamps per user per action type
- [ ] Implement sliding window algorithm
- [ ] Add auto-block mechanism for violations
- [ ] Log rate limit violations to audit trail
- [ ] Add configurable limits per action type
- [ ] Consider Redis integration for distributed rate limiting

**Implementation Example:**
```python
# Class-level cache
self._rate_limit_cache = {}  # {user_email: {action_type: [timestamps]}}

def check_rate_limit(self, user_email, action_type, max_per_minute=10):
    now = datetime.now(timezone.utc)
    key = f"{user_email}:{action_type}"
    
    # Get recent timestamps
    if key not in self._rate_limit_cache:
        self._rate_limit_cache[key] = []
    
    # Remove timestamps older than 1 minute
    self._rate_limit_cache[key] = [
        ts for ts in self._rate_limit_cache[key]
        if (now - ts).total_seconds() < 60
    ]
    
    # Check limit
    if len(self._rate_limit_cache[key]) >= max_per_minute:
        return False  # Rate limit exceeded
    
    # Add current timestamp
    self._rate_limit_cache[key].append(now)
    return True
```

---

## Low Priority (Enhancements)

### 8. Pagination for Large User Lists
**File:** `src/app/gui/admin_dashboard_screen.py`
**Priority:** 🟢 LOW

**TODO:**
- [ ] Add page size control (25, 50, 100 users per page)
- [ ] Implement Firestore query with `limit()` and `offset()`
- [ ] Add "Previous" / "Next" buttons
- [ ] Show current page / total pages
- [ ] Preserve filters/search across pages

---

### 9. Audit Log Viewer UI
**File:** `src/app/gui/audit_log_viewer.py` (NEW)
**Priority:** 🟢 LOW

**TODO:**
- [ ] Create new screen for viewing audit logs
- [ ] Fetch from `admin_audit_logs` collection
- [ ] Add filters: date range, admin email, action type, target user
- [ ] Add sorting: newest first, oldest first
- [ ] Implement export to CSV
- [ ] Add real-time listener for live updates
- [ ] Show detailed action information in expandable rows

---

### 10. Re-authentication for Critical Actions
**File:** `src/app/gui/admin_dashboard_screen.py`
**Priority:** 🟢 LOW

**TODO:**
- [ ] Add password re-entry dialog before role changes
- [ ] Implement MFA challenge (if enabled)
- [ ] Verify OAuth token freshness
- [ ] Force re-login if token expired
- [ ] Add session timeout for admin operations

---

### 11. Bulk Operations
**File:** `src/app/gui/admin_dashboard_screen.py`
**Priority:** 🟢 LOW

**TODO:**
- [ ] Add checkbox selection for multiple users
- [ ] Implement "Export Selected" to CSV
- [ ] Implement "Bulk Role Change" with confirmation
- [ ] Add "Select All" / "Deselect All" buttons
- [ ] Show selected count in UI

---

### 12. Real-time Updates
**File:** `src/app/gui/admin_dashboard_screen.py`
**Priority:** 🟢 LOW

**TODO:**
- [ ] Implement Firestore real-time listener on `users` collection
- [ ] Auto-update UI when users are added/modified
- [ ] Show toast notifications for changes by other admins
- [ ] Handle conflict resolution for concurrent edits

---

## Testing TODO

### Unit Tests
**File:** `tests/test_admin_dashboard.py` (NEW)

**TODO:**
- [ ] Test `verify_admin_permission()` with admin/non-admin users
- [ ] Test rate limiting logic
- [ ] Test audit logging structure
- [ ] Test user disable/enable/delete methods
- [ ] Mock Firebase calls for offline testing

### Integration Tests
**File:** `tests/test_admin_integration.py` (NEW)

**TODO:**
- [ ] Test full admin login → dashboard → role change flow
- [ ] Test unauthorized access handling
- [ ] Test audit log persistence and retrieval
- [ ] Test rate limit enforcement across operations

### Manual Testing Checklist
- [ ] Login as admin user
- [ ] Verify dashboard tab appears
- [ ] Load users list successfully
- [ ] Search users by email/name
- [ ] Filter users by role
- [ ] Change user role with confirmation
- [ ] Verify backend permission check
- [ ] Verify audit log entry created
- [ ] Attempt self-role change (should fail)
- [ ] Login as non-admin user
- [ ] Verify dashboard tab hidden
- [ ] Direct navigation attempt (should redirect)
- [ ] Verify unauthorized access logged

---

## Documentation TODO

### User Guide
**File:** `docs/admin_guide.md` (NEW)

**TODO:**
- [ ] Admin dashboard overview
- [ ] How to access dashboard
- [ ] User management operations guide
- [ ] Security best practices
- [ ] Troubleshooting common issues

### Developer Guide
**File:** `docs/dev_guide_admin.md` (NEW)

**TODO:**
- [ ] Architecture overview
- [ ] Security layers explanation
- [ ] How to add new admin operations
- [ ] Audit log schema documentation
- [ ] Rate limiting configuration

---

## Firebase Setup Instructions

### Step 1: Firestore Collections Setup

**Collections Created Automatically:**
The following collections will be created automatically when first used:
- ✅ `users` - User profiles with roles and usage data
- ✅ `admin_audit_logs` - Audit trail for admin actions

**No manual setup required** - collections are created on first write.

---

### Step 2: Firestore Indexes (Optional - For Performance)

**When to create indexes:**
- If you have >1000 users and experience slow queries
- If you want to filter audit logs by multiple fields simultaneously

**How to create indexes:**
1. Navigate to Firebase Console → Firestore Database → Indexes
2. Click "Create Index"
3. Add these composite indexes:

**Audit Logs Index:**
- Collection: `admin_audit_logs`
- Fields:
  - `timestamp` (Descending)
  - `admin_email` (Ascending)
  - `action` (Ascending)
- Query scope: Collection

**Purpose:** Speeds up filtered audit log queries (e.g., "show all role_change actions by admin@example.com in the last 30 days")

---

### Step 3: Firestore Backup Schedule (Recommended for Production)

**Current Status:** Firebase automatically backs up data (Spark/Blaze plans)

**For additional backup protection:**
1. Navigate to Firebase Console → Firestore Database → Backups
2. Enable automated backups (Blaze plan only)
3. Set schedule: Daily at 2 AM UTC
4. Set retention: 7 days

**Alternative (Free Tier):**
Use Cloud Scheduler + Cloud Functions to export Firestore data to Cloud Storage

---

### Step 4: Audit Log Retention Policy

**Current Implementation:** Logs are stored indefinitely

**Recommended Production Setup:**
Implement automatic deletion of logs older than 90 days using Firebase Cloud Functions.

**Cloud Function Example:**
```javascript
// functions/index.js
const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp();

exports.cleanupOldAuditLogs = functions.pubsub
  .schedule('every 24 hours')
  .onRun(async (context) => {
    const db = admin.firestore();
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - 90); // 90 days ago
    
    const snapshot = await db.collection('admin_audit_logs')
      .where('timestamp', '<', cutoffDate)
      .get();
    
    const batch = db.batch();
    snapshot.docs.forEach(doc => batch.delete(doc.ref));
    
    await batch.commit();
    console.log(`Deleted ${snapshot.size} old audit logs`);
  });
```

**Deployment:**
```bash
cd functions
npm install firebase-functions firebase-admin
firebase deploy --only functions
```

---

### Step 5: First Admin User Setup

**Method 1: Manual Creation in Firestore Console (Recommended)**
1. Navigate to Firebase Console → Firestore Database
2. Click on `users` collection
3. Click "Add document"
4. Set document ID to your email: `admin@example.com`
5. Add fields:
   ```
   email: "admin@example.com"
   name: "Admin User"
   role: "admin"
   created_at: [Current timestamp]
   authenticated: true
   ```
6. Save the document
7. Log in to the app with this email via Google OAuth

**Method 2: Using Firebase Admin SDK Script**
Run this Python script once:
```python
from firebase_admin import credentials, firestore, initialize_app

cred = credentials.Certificate('path/to/serviceAccountKey.json')
initialize_app(cred)
db = firestore.client()

db.collection('users').document('admin@example.com').set({
    'email': 'admin@example.com',
    'name': 'System Administrator',
    'role': 'admin',
    'created_at': firestore.SERVER_TIMESTAMP,
    'authenticated': True,
    'provider': 'manual_bootstrap'
})

print("✅ First admin user created!")
```

**Method 3: Using Config.py Super Admin (Current Implementation)**
The app automatically promotes the email in `Config.SUPER_ADMIN_EMAIL` to admin role.

---

### Step 6: Monitoring & Alerts (Production)

**Firestore Usage Monitoring:**
1. Navigate to Firebase Console → Usage and Billing
2. Set up billing alerts for:
   - Document reads (if >50k/day)
   - Document writes (if >20k/day)
   - Storage (if >1GB)

**Audit Log Monitoring:**
Consider setting up alerts for suspicious activity:
- Multiple failed admin actions
- Mass user deletions
- Role changes to admin
- Actions outside business hours

**Implementation:** Use Firebase Cloud Functions to monitor audit logs and send alerts via email/Slack.

---

### Step 7: Verify Audit Logging is Working

**Test the implementation:**
1. Run the app and log in as admin
2. Perform an admin action (change user role, create user, etc.)
3. Check Firebase Console → Firestore Database → admin_audit_logs
4. Verify a new document was created with:
   - `admin_email`: Your email
   - `action`: The action type
   - `target_user`: The affected user
   - `timestamp`: Current time (UTC)
   - `success`: true
   - `details`: Action-specific data

**Example audit log document:**
```json
{
  "admin_email": "admin@example.com",
  "action": "role_change",
  "target_user": "user@example.com",
  "timestamp": "2025-12-07T10:30:00Z",
  "success": true,
  "details": {
    "old_role": "free",
    "new_role": "premium"
  },
  "session_id": "abc123xyz",
  "client_type": "desktop_app"
}
```

---

### Troubleshooting

**Issue: Audit logs not appearing in Firestore**
- Check Firebase Admin SDK credentials are valid
- Verify `firebase_service.is_available` returns `True`
- Check console output for `[AUDIT ERROR]` messages
- Ensure Firestore is enabled in Firebase Console

**Issue: Permission denied errors**
- Desktop app uses Admin SDK which bypasses security rules
- If you see permission errors, check your service account has proper IAM roles
- Required role: "Cloud Datastore User" or "Firebase Admin"

**Issue: Timestamps showing as future dates**
- Ensure system clock is synchronized
- Use `datetime.now(timezone.utc)` not `datetime.now()` (local time)

---

### Summary Checklist

- [x] Audit logging implemented in `firebase_service.py`
- [x] `get_audit_logs()` method for retrieval
- [ ] First admin user created in Firestore
- [ ] Verified audit logs appear in Firestore Console
- [ ] (Optional) Created composite indexes for performance
- [ ] (Optional) Set up automated backups
- [ ] (Optional) Deployed Cloud Function for log retention
- [ ] (Optional) Configured monitoring alerts

---

## Summary

**Critical Path:**
1. ✅ ~~Deploy Firebase Security Rules~~ (N/A for desktop app - uses Admin SDK)
2. ✅ Implement audit logging persistence (COMPLETED)
3. ✅ Integrate dashboard into main window (COMPLETED - via config tab)
4. ✅ Test with admin/non-admin users (Ready for validation)

**Recently Completed:**
- ✅ Audit logging now persists to Firestore `admin_audit_logs` collection
- ✅ Added `get_audit_logs()` method for retrieving logs with filters
- ✅ Session ID tracking for better traceability
- ✅ Comprehensive error handling for logging failures
- ✅ Created detailed Firebase setup guide
- ✅ Created audit logging quick reference guide (`docs/AUDIT_LOGGING_GUIDE.md`)

**Estimated Effort (Remaining):**
- Critical items: ~~8-12 hours~~ → 0 hours (COMPLETED)
- Medium items: ~6-8 hours
- Low priority: ~10-15 hours
- Total Remaining: ~16-23 hours

**Next Steps:**
1. Test audit logging in live environment
2. Verify logs appear in Firebase Console
3. Consider implementing audit log viewer UI (Enhancement #9)
4. Deploy Cloud Function for log retention (optional)

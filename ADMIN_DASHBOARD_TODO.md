# Admin Dashboard Implementation - TODO Tracker

## High Priority (Security Critical)

### 1. Firebase Security Rules
**File:** Firebase Console (Firestore Rules)
**Priority:** 🔴 CRITICAL
**Description:** Deploy server-side security rules to enforce role-based access at the database level

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Helper function to check admin role
    function isAdmin() {
      return request.auth != null && 
             request.auth.token.role == 'admin';
    }
    
    // Users collection - admins can read/write, users can read own document
    match /users/{userId} {
      allow read: if request.auth != null;
      allow write: if isAdmin();
    }
    
    // Audit logs - only admins can read
    match /admin_audit_logs/{logId} {
      allow read: if isAdmin();
      allow write: if isAdmin();
    }
  }
}
```

**Steps:**
1. Navigate to Firebase Console → Firestore Database → Rules
2. Copy the rules above
3. Test in Firebase Rules Playground
4. Deploy to production

---

### 2. Audit Logging Persistence
**File:** `src/access_control/firebase_service.py`
**Priority:** 🔴 CRITICAL
**Function:** `log_admin_action()`

**Current Status:** Skeleton implemented, prints to console only

**TODO:**
- [ ] Uncomment Firestore write in `log_admin_action()`
- [ ] Create `admin_audit_logs` collection schema
- [ ] Capture IP address from request context
- [ ] Capture session ID from session_manager
- [ ] Add error handling for logging failures
- [ ] Implement log retention policy (auto-delete logs >90 days)

**Implementation:**
```python
# In log_admin_action()
self.db.collection('admin_audit_logs').add(log_entry)
```

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

## Medium Priority (Functionality)

### 4. Backend Permission Verification
**File:** `src/app/gui/admin_dashboard_screen.py`
**Priority:** 🟠 HIGH
**Function:** `_verify_backend_permission()`

**Current Status:** Trusts session_manager only

**TODO:**
- [ ] Call `firebase_service.verify_admin_permission(email)`
- [ ] Add session token validation
- [ ] Verify token hasn't expired
- [ ] Add IP whitelist check (if configured)

---

### 5. User Disable/Enable Functionality
**File:** `src/app/gui/admin_dashboard_screen.py`
**Priority:** 🟡 MEDIUM
**Function:** `_toggle_user_status()`

**Current Status:** Shows error message, not implemented

**TODO:**
- [ ] Add confirmation dialog
- [ ] Call `firebase_service.disable_user(email)` or `enable_user(email)`
- [ ] Update UI after success
- [ ] Log action to audit trail
- [ ] Handle revoke active sessions (future)

---

### 6. User Deletion Functionality
**File:** `src/app/gui/admin_dashboard_screen.py`
**Priority:** 🟡 MEDIUM
**Function:** `_delete_user()`

**Current Status:** Shows error message, not implemented

**TODO:**
- [ ] Add strong confirmation (type email to confirm)
- [ ] Archive user data before deletion
- [ ] Call `firebase_service.delete_user(email)`
- [ ] Delete from Firebase Auth (not just Firestore)
- [ ] Handle cascade deletion of related data
- [ ] Log action to audit trail

---

### 7. Integration with Main Window
**File:** `src/app/gui/main_window.py`
**Priority:** 🟡 MEDIUM

**TODO:**
- [ ] Add "Admin Dashboard" tab to main window
- [ ] Check `session_manager.has_permission(Permission.MANAGE_USERS)`
- [ ] Only show tab if user is admin
- [ ] Handle navigation to/from dashboard
- [ ] Test with different role types

**Implementation:**
```python
# In main_window.py build() method
tabs = []

# Existing tabs
tabs.append(ft.Tab(text="Selection", content=...))
tabs.append(ft.Tab(text="Arrangement", content=...))
tabs.append(ft.Tab(text="Save/Upload", content=...))
tabs.append(ft.Tab(text="Config", content=...))

# Admin dashboard tab (conditional)
if session_manager.has_permission(Permission.MANAGE_USERS.value):
    from app.gui.admin_dashboard_screen import AdminDashboardScreen
    admin_dashboard = AdminDashboardScreen(self.page)
    admin_dashboard.load_users()  # Load on tab creation
    tabs.append(ft.Tab(
        text="Admin Dashboard",
        icon=ft.Icons.ADMIN_PANEL_SETTINGS,
        content=admin_dashboard.build()
    ))
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

## Firebase Setup TODO

### Firestore Collections
**TODO:**
- [ ] Deploy `admin_audit_logs` collection structure
- [ ] Set up indexes for query optimization
- [ ] Configure backup schedule
- [ ] Set retention policies

### Firebase Auth
**TODO:**
- [ ] Configure custom claims for role management
- [ ] Set up admin user bootstrap process
- [ ] Document first admin creation process

---

## Summary

**Critical Path:**
1. Deploy Firebase Security Rules (prevents bypass attacks)
2. Implement audit logging persistence (compliance requirement)
3. Integrate dashboard into main window (user-facing)
4. Test with admin/non-admin users (validation)

**Estimated Effort:**
- Critical items: ~8-12 hours
- Medium items: ~6-8 hours
- Low priority: ~10-15 hours
- Total: ~24-35 hours

**Dependencies:**
- Firebase Console access for rules deployment
- Admin test account for validation
- Firestore write permissions for audit logs

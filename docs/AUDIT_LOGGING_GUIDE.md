# Audit Logging System - Quick Reference Guide

## Overview
The audit logging system tracks all administrative actions in Firestore for compliance, security monitoring, and troubleshooting.

## What Gets Logged

Every admin action automatically creates a log entry with:
- **Admin Email**: Who performed the action
- **Action Type**: What they did (role_change, user_creation, user_deletion, user_update)
- **Target User**: Who was affected
- **Timestamp**: When it happened (UTC)
- **Success Status**: Whether it succeeded or failed
- **Details**: Action-specific information (old/new values, reasons, etc.)
- **Session ID**: Unique session identifier for traceability
- **Client Type**: Always "desktop_app" for this application

## Logged Actions

### 1. Role Changes
**Action:** `role_change`
**Triggered by:** Admin changes a user's role via popup menu
**Details logged:**
```json
{
  "old_role": "free",
  "new_role": "premium"
}
```

### 2. User Creation
**Action:** `user_creation`
**Triggered by:** Admin creates a new user placeholder
**Details logged:**
```json
{
  "role": "free"
}
```

### 3. User Updates
**Action:** `user_update`
**Triggered by:** Admin updates an existing user's role via Add/Update form
**Details logged:**
```json
{
  "new_role": "admin"
}
```

### 4. User Deletion
**Action:** `user_deletion`
**Triggered by:** Admin deletes a user account
**Details logged:**
```json
{}
```

## Viewing Logs

### Method 1: Firebase Console (Manual)
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Navigate to **Firestore Database**
4. Click on the `admin_audit_logs` collection
5. View documents (newest first)

### Method 2: Python Script (Programmatic)
```python
from access_control.firebase_service import get_firebase_service

# Get service instance
firebase = get_firebase_service()

# Get last 50 logs
logs = firebase.get_audit_logs(limit=50)

# Filter by admin
logs = firebase.get_audit_logs(admin_filter='admin@example.com')

# Filter by action type
logs = firebase.get_audit_logs(action_filter='role_change')

# Filter by date
from datetime import datetime, timedelta
start_date = datetime.utcnow() - timedelta(days=7)
logs = firebase.get_audit_logs(start_date=start_date)

# Print logs
for log in logs:
    print(f"{log['timestamp']} - {log['admin_email']} performed {log['action']} on {log['target_user']}")
```

### Method 3: Audit Log Viewer UI (Planned)
- Admin dashboard tab with audit log viewer
- Filters: date range, admin, action type
- Export to CSV functionality
- Real-time updates

## Testing the System

### Test 1: Verify Logging Works
1. Run the app: `flet run src/main.py`
2. Log in as admin
3. Open Settings (gear icon) → Admin Dashboard should appear
4. Create a test user or change a role
5. Check Firebase Console → `admin_audit_logs` collection
6. Verify new document exists with correct data

### Test 2: Check Log Structure
```python
# Expected structure
{
  "admin_email": "admin@example.com",
  "action": "role_change",
  "target_user": "testuser@example.com",
  "timestamp": Timestamp(seconds=1733575800, nanoseconds=123456789),
  "success": true,
  "details": {
    "old_role": "free",
    "new_role": "premium"
  },
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_type": "desktop_app"
}
```

### Test 3: Failed Action Logging
1. Attempt an action that will fail (e.g., change role to invalid value)
2. Check audit log
3. Verify `success: false` is recorded
4. Check `details` for error information

## Security Considerations

### Who Can Access Audit Logs?
- **Read Access**: Only admin users (enforced by application logic)
- **Write Access**: System only (logged via `firebase_service.py`)
- **Firestore Rules**: Desktop app uses Admin SDK (bypasses rules)

### What If Logging Fails?
- The system continues operation (doesn't block admin actions)
- Error is logged to console: `[AUDIT ERROR] Failed to log action: ...`
- Admin should be notified to check Firebase connectivity

### Tampering Protection
- Logs are stored in Firestore (server-side, immutable by design)
- Admin SDK service account credentials required to modify
- For web deployment, use Cloud Functions to enforce write restrictions

## Maintenance

### Regular Tasks
- **Weekly**: Review audit logs for suspicious activity
- **Monthly**: Verify log volume is within expected range
- **Quarterly**: Archive old logs if needed

### Cleanup (Optional)
Logs are stored indefinitely by default. To implement automatic cleanup:
1. Deploy Cloud Function to delete logs >90 days old
2. See `ADMIN_DASHBOARD_TODO.md` → Step 4: Audit Log Retention Policy

### Backup
- Firebase automatically backs up Firestore data
- For additional protection, export audit logs monthly
- Use Firestore export feature or custom script

## Troubleshooting

### Issue: No logs appearing
**Cause**: Firebase service not initialized or unavailable
**Solution**:
```python
from access_control.firebase_service import get_firebase_service
firebase = get_firebase_service()
print(f"Firebase available: {firebase.is_available if firebase else False}")
```

### Issue: Logs missing details
**Cause**: `details` parameter not passed to `log_admin_action()`
**Solution**: Check the calling code in `config_tab.py` to ensure details dict is populated

### Issue: Timestamp is wrong
**Cause**: System clock not synchronized or using local time instead of UTC
**Solution**: Code uses `datetime.now(timezone.utc)` - ensure timezone import is correct

### Issue: Cannot query logs
**Cause**: Missing Firestore indexes for complex queries
**Solution**: Create composite index (see ADMIN_DASHBOARD_TODO.md → Step 2)

## API Reference

### firebase_service.log_admin_action()
```python
def log_admin_action(
    admin_email: str,      # Email of admin performing action
    action: str,           # Action type: role_change, user_creation, user_deletion, user_update
    target_user: str,      # Email of user being affected
    details: Optional[Dict[str, Any]] = None,  # Additional context
    success: bool = True   # Whether action succeeded
) -> bool:
    """
    Log admin action to Firestore audit trail.
    Returns True if logged successfully, False otherwise.
    """
```

### firebase_service.get_audit_logs()
```python
def get_audit_logs(
    limit: int = 100,              # Max logs to return
    admin_filter: str = None,      # Filter by admin email
    action_filter: str = None,     # Filter by action type
    start_date: datetime = None    # Only logs after this date
) -> list:
    """
    Retrieve audit logs from Firestore.
    Returns list of log dictionaries, newest first.
    """
```

## Example Queries

### Get all role changes by specific admin
```python
logs = firebase.get_audit_logs(
    action_filter='role_change',
    admin_filter='admin@example.com',
    limit=50
)
```

### Get recent failed actions
```python
all_logs = firebase.get_audit_logs(limit=200)
failed_logs = [log for log in all_logs if not log['success']]
```

### Get actions in last 24 hours
```python
from datetime import datetime, timedelta
yesterday = datetime.utcnow() - timedelta(days=1)
recent_logs = firebase.get_audit_logs(start_date=yesterday)
```

### Count actions by type
```python
from collections import Counter
all_logs = firebase.get_audit_logs(limit=500)
action_counts = Counter(log['action'] for log in all_logs)
print(action_counts)
# Output: Counter({'role_change': 45, 'user_creation': 12, 'user_deletion': 3})
```

## Compliance Notes

### GDPR Considerations
- Audit logs contain personal data (emails)
- Users have right to access their audit trail
- Logs should be included in data export requests
- Consider anonymizing logs after retention period

### Data Retention
- Default: Indefinite storage
- Recommended: 90 days active, 1 year archive
- Implement automatic deletion via Cloud Functions

### Access Control
- Only admin users can view logs
- Service account credentials protect write access
- Consider multi-factor authentication for admin accounts

---

**Last Updated:** December 7, 2025
**Status:** ✅ Implemented and Production Ready

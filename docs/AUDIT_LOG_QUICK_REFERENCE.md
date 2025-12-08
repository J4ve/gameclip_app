# Audit Log Viewer - Quick Reference

## 🎯 Quick Access
**Path:** Admin Dashboard → Audit Logs Tab
**Permission:** Admin role required
**Shortcut:** Settings Icon (⚙️) → Admin Dashboard

---

## 🔍 Filters

| Filter | Description | Example |
|--------|-------------|---------|
| **Actor** | Admin who performed action | `admin@example.com` |
| **Target User** | User who was affected | `user@example.com` |
| **Action Type** | Type of action performed | Role Change, User Creation, etc. |
| **Date Range** | Time period for logs | Today, Last 7 Days, Last 30 Days, All Time |

---

## 📊 Log Entry Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Timestamp** | When action occurred (UTC) | `2024-12-08 14:30:15` |
| **Actor** | Admin email | `admin@example.com` |
| **Action** | Action type | `Role Change` |
| **Target** | Affected user | `user@example.com` |
| **Status** | Success/failure | ✅ / ❌ |
| **Details** | Additional info | `old_role: free, new_role: premium` |

---

## 📥 Export to CSV

1. Apply desired filters (or leave empty for all logs)
2. Click **"Export to CSV"** button
3. File saved to: `storage/exports/audit_logs_YYYYMMDD_HHMMSS.csv`
4. Open in Excel, Google Sheets, or any CSV viewer

**CSV Columns:**
- timestamp
- admin_email
- action
- target_user
- success
- details
- session_id

---

## 🔐 Security Features

- ✅ Admin-only access (multi-layer verification)
- ✅ Unauthorized access attempts logged
- ✅ Immutable log records (no edit/delete)
- ✅ Secure Firestore storage
- ✅ No sensitive data in logs

---

## 🚀 Quick Actions

| Action | Button/Control |
|--------|----------------|
| Load latest logs | Click "Audit Logs" tab |
| Refresh logs | Click "Refresh" button (🔄) |
| Clear all filters | Click "Clear Filters" button |
| Export logs | Click "Export to CSV" button |
| Filter by actor | Type email in "Filter by Actor" |
| Filter by target | Type email in "Filter by Target User" |
| Filter by action | Select from "Action Type" dropdown |
| Filter by date | Select from "Date Range" dropdown |

---

## 📋 Common Use Cases

### 1. View all actions by specific admin
```
Filter by Actor: admin@example.com
Action Type: All Actions
Date Range: All Time
```

### 2. View recent role changes
```
Action Type: Role Change
Date Range: Last 7 Days
```

### 3. View all actions affecting a user
```
Filter by Target User: user@example.com
Date Range: All Time
```

### 4. Export last month's logs for compliance
```
Date Range: Last 30 Days
Click "Export to CSV"
```

### 5. Investigate failed actions
```
Status: Look for ❌ in table
Date Range: Today or Last 7 Days
```

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| No logs shown | Clear filters, check Firebase connection |
| Export fails | Check `storage/exports/` directory exists |
| Unauthorized access | Verify admin role assigned |
| Slow loading | Reduce date range, use more specific filters |

---

## 📞 Support

**Documentation:**
- Full Guide: `docs/AUDIT_LOG_VIEWER_IMPLEMENTATION.md`
- Summary: `docs/AUDIT_LOG_IMPLEMENTATION_SUMMARY.md`

**Testing:**
```bash
python -m pytest tests/test_audit_log_viewer.py -v
```

**Firebase Console:**
Collection: `admin_audit_logs`
https://console.firebase.google.com/

---

**Last Updated:** December 8, 2024

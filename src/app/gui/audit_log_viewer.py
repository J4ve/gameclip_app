"""
Audit Log Data Service
Handles fetching and exporting audit logs from Firebase.
UI components are in admin_dashboard.py
"""

from access_control.session import session_manager
from access_control.roles import Permission
from access_control.firebase_service import get_firebase_service
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
import csv
import os


class AuditLogService:
    """Service for fetching and exporting audit logs"""
    
    def __init__(self):
        self.firebase_service = get_firebase_service()
        
        # Security: Verify admin permission
        if not self._verify_admin_access():
            raise PermissionError("Admin privileges required to view audit logs")
    
    def _verify_admin_access(self) -> bool:
        """Verify user has permission to view audit logs"""
        print(f"[DEBUG AUDIT] Checking permission for {session_manager.email}")
        print(f"[DEBUG AUDIT] Permission.MANAGE_USERS.value = {Permission.MANAGE_USERS.value}")
        
        has_perm = session_manager.has_permission(Permission.MANAGE_USERS.value)
        print(f"[DEBUG AUDIT] has_permission result: {has_perm}")
        
        if not has_perm:
            print(f"[SECURITY] Unauthorized audit log access attempt by {session_manager.email}")
            return False
        
        print(f"[SECURITY] Audit log access granted to {session_manager.email}")
        return True
    
    def fetch_logs(self, actor_filter: Optional[str] = None, target_filter: Optional[str] = None,
                   action_filter: Optional[str] = None, date_range: str = "all") -> List[Dict[str, Any]]:
        """Fetch audit logs from Firebase with filters"""
        if not self.firebase_service or not self.firebase_service.is_available:
            print("[AUDIT LOG] Firebase not available")
            return []
        
        try:
            # Get date range
            start_date, end_date = self._get_date_range(date_range)
            
            # Fetch logs from Firebase
            logs = self.firebase_service.get_audit_logs(
                limit=500,
                admin_filter=actor_filter,
                action_filter=action_filter if action_filter != "all" else None,
                target_user_filter=target_filter,
                start_date=start_date,
                end_date=end_date
            )
            
            return logs
            
        except Exception as e:
            print(f"[AUDIT LOG] Error loading logs: {e}")
            return []
    
    def _get_date_range(self, date_range: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get start and end dates based on range string"""
        now = datetime.now(timezone.utc)
        
        if date_range == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif date_range == "week":
            start_date = now - timedelta(days=7)
            end_date = now
        elif date_range == "month":
            start_date = now - timedelta(days=30)
            end_date = now
        else:  # "all" or "custom"
            start_date = None
            end_date = None
        
        return start_date, end_date
    
    def export_to_csv(self, logs_data: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Export logs to CSV file. Returns (success, message)"""
        if not logs_data:
            return False, "No logs to export"
        
        try:
            # Create exports directory if it doesn't exist
            export_dir = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "exports")
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_logs_{timestamp}.csv"
            filepath = os.path.join(export_dir, filename)
            
            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'admin_email', 'action', 'target_user', 'success', 'details', 'session_id']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for log in logs_data:
                    # Format timestamp for CSV
                    log_timestamp = log.get('timestamp')
                    if hasattr(log_timestamp, 'strftime'):
                        log_timestamp = log_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
                    
                    # Flatten details dict
                    details = log.get('details', {})
                    if isinstance(details, dict):
                        details = str(details)
                    
                    # Write row
                    writer.writerow({
                        'timestamp': log_timestamp,
                        'admin_email': log.get('admin_email', ''),
                        'action': log.get('action', ''),
                        'target_user': log.get('target_user', ''),
                        'success': log.get('success', True),
                        'details': details,
                        'session_id': log.get('session_id', '')
                    })
            
            print(f"[AUDIT LOG] Exported {len(logs_data)} logs to {filepath}")
            return True, f"Exported {len(logs_data)} logs to {filename}"
            
        except Exception as e:
            print(f"[AUDIT LOG] Export error: {e}")
            return False, f"Failed to export logs: {str(e)}"

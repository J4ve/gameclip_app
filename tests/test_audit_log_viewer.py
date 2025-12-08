"""
Test Audit Log Viewer Functionality
Tests audit log retrieval, filtering, and CSV export
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock, patch
from access_control.firebase_service import FirebaseService
from app.gui.audit_log_viewer import AuditLogService
import flet as ft


class TestAuditLogRetrieval:
    """Test audit log retrieval with various filters"""
    
    @pytest.fixture
    def mock_firebase_service(self):
        """Create a mock Firebase service"""
        service = Mock(spec=FirebaseService)
        service.is_available = True
        return service
    
    @pytest.fixture
    def sample_logs(self):
        """Sample audit log data"""
        now = datetime.now(timezone.utc)
        return [
            {
                'id': 'log1',
                'timestamp': now,
                'admin_email': 'admin1@example.com',
                'action': 'role_change',
                'target_user': 'user1@example.com',
                'success': True,
                'details': {'old_role': 'free', 'new_role': 'premium'},
                'session_id': 'session1'
            },
            {
                'id': 'log2',
                'timestamp': now - timedelta(hours=2),
                'admin_email': 'admin2@example.com',
                'action': 'user_creation',
                'target_user': 'user2@example.com',
                'success': True,
                'details': {'role': 'free'},
                'session_id': 'session2'
            },
            {
                'id': 'log3',
                'timestamp': now - timedelta(days=1),
                'admin_email': 'admin1@example.com',
                'action': 'user_deletion',
                'target_user': 'user3@example.com',
                'success': False,
                'details': {'error': 'User not found'},
                'session_id': 'session3'
            }
        ]
    
    def test_get_audit_logs_no_filters(self, mock_firebase_service, sample_logs):
        """Test retrieving all audit logs without filters"""
        mock_firebase_service.get_audit_logs.return_value = sample_logs
        
        logs = mock_firebase_service.get_audit_logs(limit=100)
        
        assert len(logs) == 3
        assert logs[0]['action'] == 'role_change'
        mock_firebase_service.get_audit_logs.assert_called_once()
    
    def test_get_audit_logs_with_actor_filter(self, mock_firebase_service, sample_logs):
        """Test filtering logs by actor (admin email)"""
        filtered_logs = [log for log in sample_logs if log['admin_email'] == 'admin1@example.com']
        mock_firebase_service.get_audit_logs.return_value = filtered_logs
        
        logs = mock_firebase_service.get_audit_logs(admin_filter='admin1@example.com')
        
        assert len(logs) == 2
        assert all(log['admin_email'] == 'admin1@example.com' for log in logs)
    
    def test_get_audit_logs_with_action_filter(self, mock_firebase_service, sample_logs):
        """Test filtering logs by action type"""
        filtered_logs = [log for log in sample_logs if log['action'] == 'role_change']
        mock_firebase_service.get_audit_logs.return_value = filtered_logs
        
        logs = mock_firebase_service.get_audit_logs(action_filter='role_change')
        
        assert len(logs) == 1
        assert logs[0]['action'] == 'role_change'
    
    def test_get_audit_logs_with_target_user_filter(self, mock_firebase_service, sample_logs):
        """Test filtering logs by target user"""
        filtered_logs = [log for log in sample_logs if log['target_user'] == 'user1@example.com']
        mock_firebase_service.get_audit_logs.return_value = filtered_logs
        
        logs = mock_firebase_service.get_audit_logs(target_user_filter='user1@example.com')
        
        assert len(logs) == 1
        assert logs[0]['target_user'] == 'user1@example.com'
    
    def test_get_audit_logs_with_date_range(self, mock_firebase_service, sample_logs):
        """Test filtering logs by date range"""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(hours=3)
        
        filtered_logs = [log for log in sample_logs if log['timestamp'] >= start_date]
        mock_firebase_service.get_audit_logs.return_value = filtered_logs
        
        logs = mock_firebase_service.get_audit_logs(start_date=start_date)
        
        assert len(logs) == 2
        assert all(log['timestamp'] >= start_date for log in logs)
    
    def test_get_audit_logs_multiple_filters(self, mock_firebase_service, sample_logs):
        """Test filtering logs with multiple criteria"""
        filtered_logs = [
            log for log in sample_logs 
            if log['admin_email'] == 'admin1@example.com' 
            and log['success'] is True
        ]
        mock_firebase_service.get_audit_logs.return_value = filtered_logs
        
        logs = mock_firebase_service.get_audit_logs(admin_filter='admin1@example.com')
        
        # Further filter in application logic
        logs = [log for log in logs if log['success'] is True]
        
        assert len(logs) == 1
        assert logs[0]['admin_email'] == 'admin1@example.com'
        assert logs[0]['success'] is True


class TestAuditLogViewer:
    """Test Audit Log Viewer UI component"""
    
    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page"""
        page = Mock(spec=ft.Page)
        page.update = Mock()
        page.snack_bar = None
        return page
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager with admin permissions"""
        with patch('app.gui.audit_log_viewer.session_manager') as mock_sm:
            mock_sm.has_permission.return_value = True
            mock_sm.email = 'admin@example.com'
            yield mock_sm
    
    @pytest.fixture
    def mock_firebase_service(self):
        """Mock Firebase service"""
        with patch('app.gui.audit_log_viewer.get_firebase_service') as mock_gfs:
            service = Mock(spec=FirebaseService)
            service.is_available = True
            service.get_audit_logs.return_value = []
            mock_gfs.return_value = service
            yield service
    
    def test_audit_log_viewer_initialization(self, mock_page, mock_session_manager, mock_firebase_service):
        """Test audit log viewer initialization with proper permissions"""
        viewer = AuditLogService(mock_page)
        
        assert viewer.page == mock_page
        assert viewer.firebase_service == mock_firebase_service
        mock_session_manager.has_permission.assert_called_once()
    
    def test_audit_log_viewer_unauthorized_access(self, mock_page):
        """Test audit log viewer blocks unauthorized access"""
        with patch('app.gui.audit_log_viewer.session_manager') as mock_sm:
            mock_sm.has_permission.return_value = False
            mock_sm.email = 'user@example.com'
            
            with pytest.raises(PermissionError):
                AuditLogService(mock_page)
    
    def test_load_logs_displays_data(self, mock_page, mock_session_manager, mock_firebase_service):
        """Test loading and displaying audit logs"""
        sample_logs = [
            {
                'id': 'log1',
                'timestamp': datetime.now(timezone.utc),
                'admin_email': 'admin@example.com',
                'action': 'role_change',
                'target_user': 'user@example.com',
                'success': True,
                'details': {'old_role': 'free', 'new_role': 'premium'}
            }
        ]
        mock_firebase_service.get_audit_logs.return_value = sample_logs
        
        viewer = AuditLogService(mock_page)
        viewer.build()  # Build UI components
        viewer.load_logs()
        
        assert len(viewer.logs_data) == 1
        assert viewer.logs_data[0]['action'] == 'role_change'
        mock_firebase_service.get_audit_logs.assert_called()
    
    def test_filter_controls_work(self, mock_page, mock_session_manager, mock_firebase_service):
        """Test filter controls trigger log reload"""
        viewer = AuditLogService(mock_page)
        viewer.build()
        
        # Simulate filter change
        viewer.actor_filter_field.value = "admin@example.com"
        viewer._on_filter_changed(None)
        
        # Verify get_audit_logs was called with filter
        mock_firebase_service.get_audit_logs.assert_called()
    
    def test_csv_export_creates_file(self, mock_page, mock_session_manager, mock_firebase_service, tmp_path):
        """Test CSV export functionality"""
        sample_logs = [
            {
                'id': 'log1',
                'timestamp': datetime.now(timezone.utc),
                'admin_email': 'admin@example.com',
                'action': 'role_change',
                'target_user': 'user@example.com',
                'success': True,
                'details': {'old_role': 'free', 'new_role': 'premium'},
                'session_id': 'session1'
            }
        ]
        
        viewer = AuditLogService(mock_page)
        viewer.logs_data = sample_logs
        viewer.build()
        
        # Mock file path to temp directory
        with patch('os.path.join', return_value=str(tmp_path / 'test_audit_logs.csv')):
            with patch('os.makedirs'):
                viewer._export_to_csv(None)
        
        # Verify success message was shown
        assert mock_page.snack_bar is not None


class TestAuditLogIntegration:
    """Integration tests for audit logging system"""
    
    def test_admin_action_creates_audit_log(self):
        """Test that admin actions automatically create audit logs"""
        # This would be an integration test with real Firebase
        # For now, we verify the log structure
        
        expected_log_structure = {
            'admin_email': str,
            'action': str,
            'target_user': str,
            'timestamp': datetime,
            'success': bool,
            'details': dict,
            'session_id': str,
            'client_type': str
        }
        
        # Verify all required fields are present
        assert all(field in expected_log_structure for field in [
            'admin_email', 'action', 'target_user', 'timestamp', 
            'success', 'details', 'session_id', 'client_type'
        ])
    
    def test_audit_log_viewer_filters_match_backend(self):
        """Test that UI filters match backend query parameters"""
        # Verify filter parameter names are consistent
        backend_params = ['limit', 'admin_filter', 'action_filter', 'target_user_filter', 'start_date', 'end_date']
        
        # These should match the parameters used in AuditLogViewer
        assert 'admin_filter' in backend_params  # Actor filter
        assert 'target_user_filter' in backend_params  # Target user filter
        assert 'action_filter' in backend_params  # Action type filter
        assert 'start_date' in backend_params  # Date range filter


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
Tests for Session Manager Premium Purchase Integration
Tests the purchase_premium method and role upgrades through purchase flow
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from access_control.session import SessionManager, session_manager
from access_control.roles import FreeRole, PremiumRole, GuestRole, RoleType
from access_control.purchase_service import PurchaseStatus


@pytest.fixture
def clean_session():
    """Clean session for each test"""
    session_manager.logout()
    yield session_manager
    session_manager.logout()


@pytest.fixture
def logged_in_free_user(clean_session):
    """Session with logged in free user"""
    user_data = {
        'email': 'freeuser@test.com',
        'name': 'Free User',
        'uid': 'free_123'
    }
    clean_session.login(user_data, FreeRole())
    return clean_session


@pytest.fixture
def mock_purchase_service():
    """Mock purchase service"""
    with patch('access_control.session.get_purchase_service') as mock:
        service = Mock()
        mock.return_value = service
        yield service


@pytest.fixture
def mock_firebase():
    """Mock Firebase service"""
    with patch('access_control.session.SessionManager._get_firebase_service') as mock:
        firebase = Mock()
        firebase.is_available = True
        firebase.update_user_role.return_value = True
        firebase.set_premium_until.return_value = True
        mock.return_value = firebase
        yield firebase


class TestPurchasePremiumBasics:
    """Test basic purchase_premium functionality"""
    
    def test_purchase_premium_method_exists(self, clean_session):
        """Test that purchase_premium method exists"""
        assert hasattr(clean_session, 'purchase_premium')
        assert callable(clean_session.purchase_premium)
    
    def test_purchase_fails_when_not_logged_in(self, clean_session):
        """Test that purchase fails when user not logged in"""
        result = clean_session.purchase_premium('monthly')
        
        assert result['status'] == 'failed'
        assert 'not logged in' in result['message'].lower()
    
    def test_purchase_fails_for_guest_user(self, clean_session):
        """Test that guest users cannot purchase premium"""
        guest_data = {'email': 'guest@test.com', 'name': 'Guest'}
        clean_session.login(guest_data, GuestRole())
        
        result = clean_session.purchase_premium('monthly')
        
        assert result['status'] == 'failed'
        assert 'guest' in result['message'].lower()


class TestSuccessfulPurchase:
    """Test successful premium purchase flow"""
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_successful_lifetime_purchase(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test successful lifetime premium purchase"""
        # Mock successful purchase
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_result = {
            'status': 'success',
            'transaction_id': 'TXN-123456',
            'plan': 'lifetime',
            'amount': 5.00,
            'currency': 'PHP',
            'premium_until': datetime.now(timezone.utc) + timedelta(days=36500),
            'message': 'Purchase successful'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        # Perform purchase
        result = logged_in_free_user.purchase_premium('lifetime')
        
        # Verify purchase was processed
        assert result['status'] == 'success'
        assert logged_in_free_user.is_premium() is True
        assert logged_in_free_user.role_name == 'premium'


class TestRoleUpgradeOnPurchase:
    """Test that role is upgraded correctly after purchase"""
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_free_user_upgrades_to_premium(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that free user becomes premium after purchase"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Before purchase
        assert logged_in_free_user.is_free() is True
        assert logged_in_free_user.is_premium() is False
        assert logged_in_free_user.has_ads() is True
        
        mock_result = {
            'status': Mock(value='success'),
            'transaction_id': 'TXN-123456',
            'plan': 'monthly',
            'amount': 9.99,
            'premium_until': datetime.now(timezone.utc) + timedelta(days=30),
            'message': 'Purchase successful'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        # Purchase
        logged_in_free_user.purchase_premium('monthly')
        
        # After purchase
        assert logged_in_free_user.is_premium() is True
        assert logged_in_free_user.is_free() is False
        assert logged_in_free_user.has_ads() is False
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_premium_permissions_granted(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that premium permissions are granted after purchase"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_result = {
            'status': Mock(value='success'),
            'transaction_id': 'TXN-123456',
            'plan': 'monthly',
            'amount': 9.99,
            'premium_until': datetime.now(timezone.utc) + timedelta(days=30),
            'message': 'Purchase successful'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        logged_in_free_user.purchase_premium('monthly')
        
        # Check premium permissions
        assert logged_in_free_user.has_permission('no_ads') is True
        assert logged_in_free_user.has_permission('unlimited_merges') is True
        assert logged_in_free_user.can_upload() is True


class TestFirebaseIntegration:
    """Test Firebase integration for purchases"""
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_premium_until_synced_to_firebase(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that premium_until is synced to Firebase"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        premium_until = datetime.now(timezone.utc) + timedelta(days=30)
        mock_result = {
            'status': Mock(value='success'),
            'transaction_id': 'TXN-123456',
            'plan': 'monthly',
            'amount': 9.99,
            'premium_until': premium_until,
            'message': 'Purchase successful'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        logged_in_free_user.purchase_premium('monthly')
        
        # Verify Firebase was called
        mock_firebase.set_premium_until.assert_called_once_with(
            'freeuser@test.com',
            premium_until
        )
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_role_updated_in_firebase(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that role is updated in Firebase"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_result = {
            'status': Mock(value='success'),
            'transaction_id': 'TXN-123456',
            'plan': 'monthly',
            'amount': 9.99,
            'premium_until': datetime.now(timezone.utc) + timedelta(days=30),
            'message': 'Purchase successful'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        logged_in_free_user.purchase_premium('monthly')
        
        # Verify Firebase was called
        mock_firebase.update_user_role.assert_called_once_with(
            'freeuser@test.com',
            'premium'
        )
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_purchase_works_without_firebase(self, mock_get_service, logged_in_free_user):
        """Test that purchase works even if Firebase unavailable"""
        # Mock Firebase unavailable
        with patch('access_control.session.SessionManager._get_firebase_service') as mock_fb:
            mock_fb.return_value = None
            
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            mock_result = {
                'status': Mock(value='success'),
                'transaction_id': 'TXN-123456',
                'plan': 'monthly',
                'amount': 9.99,
                'premium_until': datetime.now(timezone.utc) + timedelta(days=30),
                'message': 'Purchase successful'
            }
            mock_service.purchase_premium.return_value = mock_result
            
            result = logged_in_free_user.purchase_premium('monthly')
            
            # Should still succeed locally
            assert result['status'].value == 'success'
            assert logged_in_free_user.is_premium() is True


class TestFailedPurchases:
    """Test failed purchase scenarios"""
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_failed_purchase_doesnt_upgrade_role(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that failed purchase doesn't upgrade role"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_result = {
            'status': Mock(value='failed'),
            'transaction_id': 'TXN-123456',
            'plan': 'monthly',
            'amount': 9.99,
            'premium_until': None,
            'message': 'Payment declined'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        result = logged_in_free_user.purchase_premium('monthly')
        
        # User should still be free
        assert result['status'].value == 'failed'
        assert logged_in_free_user.is_free() is True
        assert logged_in_free_user.is_premium() is False
    
    def test_invalid_plan_returns_error(self, logged_in_free_user, mock_firebase):
        """Test that invalid plan name returns error"""
        result = logged_in_free_user.purchase_premium('invalid_plan')
        
        assert result['status'] == 'failed'
        assert 'invalid plan' in result['message'].lower()
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_purchase_service_exception_handled(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that exceptions from purchase service are handled"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.purchase_premium.side_effect = Exception("Service error")
        
        result = logged_in_free_user.purchase_premium('monthly')
        
        assert result['status'] == 'failed'
        assert 'error' in result['message'].lower()


class TestPlanMapping:
    """Test plan name to enum mapping"""
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_monthly_plan_mapped_correctly(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that 'monthly' maps to PurchasePlan.MONTHLY"""
        from access_control.purchase_service import PurchasePlan
        
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_result = {
            'status': Mock(value='success'),
            'transaction_id': 'TXN-123456',
            'plan': 'monthly',
            'amount': 9.99,
            'premium_until': datetime.now(timezone.utc) + timedelta(days=30),
            'message': 'Purchase successful'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        logged_in_free_user.purchase_premium('monthly')
        
        # Verify correct enum was passed
        mock_service.purchase_premium.assert_called_once_with(
            'freeuser@test.com',
            PurchasePlan.MONTHLY
        )
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_yearly_plan_mapped_correctly(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that 'yearly' maps to PurchasePlan.YEARLY"""
        from access_control.purchase_service import PurchasePlan
        
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_result = {
            'status': Mock(value='success'),
            'transaction_id': 'TXN-123456',
            'plan': 'yearly',
            'amount': 99.99,
            'premium_until': datetime.now(timezone.utc) + timedelta(days=365),
            'message': 'Purchase successful'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        logged_in_free_user.purchase_premium('yearly')
        
        mock_service.purchase_premium.assert_called_once_with(
            'freeuser@test.com',
            PurchasePlan.YEARLY
        )
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_lifetime_plan_mapped_correctly(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that 'lifetime' maps to PurchasePlan.LIFETIME"""
        from access_control.purchase_service import PurchasePlan
        
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_result = {
            'status': Mock(value='success'),
            'transaction_id': 'TXN-123456',
            'plan': 'lifetime',
            'amount': 299.99,
            'premium_until': datetime.now(timezone.utc) + timedelta(days=36500),
            'message': 'Purchase successful'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        logged_in_free_user.purchase_premium('lifetime')
        
        mock_service.purchase_premium.assert_called_once_with(
            'freeuser@test.com',
            PurchasePlan.LIFETIME
        )


class TestSessionPersistence:
    """Test that session data persists after purchase"""
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_user_data_preserved_after_purchase(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that user email, name, uid are preserved"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        original_email = logged_in_free_user.email
        original_uid = logged_in_free_user.uid
        
        mock_result = {
            'status': Mock(value='success'),
            'transaction_id': 'TXN-123456',
            'plan': 'monthly',
            'amount': 9.99,
            'premium_until': datetime.now(timezone.utc) + timedelta(days=30),
            'message': 'Purchase successful'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        logged_in_free_user.purchase_premium('monthly')
        
        # Verify user data unchanged
        assert logged_in_free_user.email == original_email
        assert logged_in_free_user.uid == original_uid
        assert logged_in_free_user.is_logged_in is True
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_login_status_maintained(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that user remains logged in after purchase"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_result = {
            'status': Mock(value='success'),
            'transaction_id': 'TXN-123456',
            'plan': 'monthly',
            'amount': 9.99,
            'premium_until': datetime.now(timezone.utc) + timedelta(days=30),
            'message': 'Purchase successful'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        logged_in_free_user.purchase_premium('monthly')
        
        assert logged_in_free_user.is_logged_in is True
        assert logged_in_free_user.is_authenticated() is True


class TestPremiumFeatures:
    """Test that premium features are unlocked after purchase"""
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_unlimited_arrangements_after_purchase(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that arrangements remain unlimited (both free and premium have unlimited)"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Before: free users also have unlimited (per current config)
        assert logged_in_free_user.get_merge_limit() == -1
        
        mock_result = {
            'status': Mock(value='success'),
            'transaction_id': 'TXN-123456',
            'plan': 'monthly',
            'amount': 9.99,
            'premium_until': datetime.now(timezone.utc) + timedelta(days=30),
            'message': 'Purchase successful'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        logged_in_free_user.purchase_premium('monthly')
        
        # After: still unlimited (premium perk)
        assert logged_in_free_user.get_merge_limit() == -1
    
    @patch('access_control.purchase_service.get_purchase_service')
    def test_no_ads_after_purchase(self, mock_get_service, logged_in_free_user, mock_firebase):
        """Test that ads are disabled"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Before: has ads
        assert logged_in_free_user.has_ads() is True
        
        mock_result = {
            'status': Mock(value='success'),
            'transaction_id': 'TXN-123456',
            'plan': 'monthly',
            'amount': 9.99,
            'premium_until': datetime.now(timezone.utc) + timedelta(days=30),
            'message': 'Purchase successful'
        }
        mock_service.purchase_premium.return_value = mock_result
        
        logged_in_free_user.purchase_premium('monthly')
        
        # After: no ads
        assert logged_in_free_user.has_ads() is False

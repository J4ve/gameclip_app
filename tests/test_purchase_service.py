"""
Tests for Purchase Service - Mock Premium Purchase API
Tests premium subscription purchasing, transaction management, and plan features
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from access_control.purchase_service import (
    PurchaseService,
    PurchaseStatus,
    PurchasePlan,
    get_purchase_service,
    reset_purchase_service,
)


@pytest.fixture
def purchase_service():
    """Create a fresh purchase service for testing"""
    reset_purchase_service()
    service = PurchaseService(mock_mode=True)
    return service


@pytest.fixture
def mock_user_email():
    """Mock user email for testing"""
    return "test@example.com"


class TestPurchaseServiceInitialization:
    """Test purchase service initialization"""
    
    def test_service_initializes_in_mock_mode(self, purchase_service):
        """Test that service initializes in mock mode"""
        assert purchase_service.mock_mode is True
        assert purchase_service.transaction_history == []
        assert purchase_service._failure_rate == 0.0
    
    def test_service_can_initialize_in_real_mode(self):
        """Test that service can initialize in real mode"""
        service = PurchaseService(mock_mode=False)
        assert service.mock_mode is False
    
    def test_singleton_returns_same_instance(self):
        """Test that get_purchase_service returns same instance"""
        reset_purchase_service()
        service1 = get_purchase_service()
        service2 = get_purchase_service()
        assert service1 is service2
    
    def test_reset_clears_singleton(self):
        """Test that reset creates new instance"""
        service1 = get_purchase_service()
        reset_purchase_service()
        service2 = get_purchase_service()
        assert service1 is not service2


class TestPurchasePlans:
    """Test purchase plan configuration"""
    
    def test_lifetime_plan_pricing(self, purchase_service):
        """Test lifetime plan has correct price"""
        assert PurchaseService.PRICES[PurchasePlan.LIFETIME] == 5.00
    
    def test_lifetime_duration(self, purchase_service):
        """Test lifetime plan duration (100 years)"""
        assert PurchaseService.DURATIONS[PurchasePlan.LIFETIME] == timedelta(days=36500)
    
    def test_get_plan_info_returns_details(self, purchase_service):
        """Test get_plan_info returns all plan details"""
        info = PurchaseService.get_plan_info(PurchasePlan.LIFETIME)
        
        assert info['plan'] == 'lifetime'
        assert info['price'] == 5.00
        assert info['currency'] == 'PHP'
        assert info['duration_days'] == 36500
        assert 'description' in info
        assert 'features' in info
        assert len(info['features']) > 0
    
    def test_get_all_plans_returns_one(self, purchase_service):
        """Test get_all_plans returns single lifetime plan"""
        plans = PurchaseService.get_all_plans()
        
        assert len(plans) == 1
        assert plans[0]['plan'] == 'lifetime'
        assert plans[0]['price'] == 5.00
        assert plans[0]['currency'] == 'PHP'


class TestSuccessfulPurchases:
    """Test successful purchase transactions"""
    
    def test_purchase_lifetime_succeeds(self, purchase_service, mock_user_email):
        """Test purchasing lifetime plan"""
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        
        assert result['status'] == PurchaseStatus.SUCCESS
        assert result['user_email'] == mock_user_email
        assert result['plan'] == 'lifetime'
        assert result['amount'] == 5.00
        assert result['currency'] == 'PHP'
        assert 'transaction_id' in result
        assert 'premium_until' in result
        assert result['premium_until'] is not None
    
    def test_successful_purchase_sets_premium_until(self, purchase_service, mock_user_email):
        """Test that successful purchase sets correct premium expiration (100 years)"""
        before = datetime.now(timezone.utc)
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        after = datetime.now(timezone.utc)
        
        premium_until = result['premium_until']
        expected_min = before + timedelta(days=36500)
        expected_max = after + timedelta(days=36500)
        
        assert premium_until >= expected_min
        assert premium_until <= expected_max
    
    def test_transaction_gets_unique_id(self, purchase_service, mock_user_email):
        """Test that each transaction gets unique ID"""
        result1 = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        result2 = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        
        assert result1['transaction_id'] != result2['transaction_id']
    
    def test_purchase_stored_in_history(self, purchase_service, mock_user_email):
        """Test that purchases are stored in transaction history"""
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        
        assert len(purchase_service.transaction_history) == 1
        assert purchase_service.transaction_history[0] == result
    
    def test_multiple_purchases_stored(self, purchase_service, mock_user_email):
        """Test that multiple purchases are all stored"""
        purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        
        assert len(purchase_service.transaction_history) == 2


class TestFailedPurchases:
    """Test failed purchase scenarios"""
    
    def test_purchase_fails_with_failure_rate(self, purchase_service, mock_user_email):
        """Test that purchase can fail based on failure rate"""
        purchase_service.set_failure_rate(1.0)  # Always fail
        
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        
        assert result['status'] == PurchaseStatus.FAILED
        assert 'failed' in result['message'].lower()
        assert result['premium_until'] is None
    
    def test_real_mode_returns_not_implemented(self, mock_user_email):
        """Test that real mode returns not implemented error"""
        service = PurchaseService(mock_mode=False)
        result = service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        
        assert result['status'] == PurchaseStatus.FAILED
        assert 'not implemented' in result['message'].lower()
    
    def test_failure_rate_can_be_set(self, purchase_service):
        """Test setting failure rate"""
        purchase_service.set_failure_rate(0.5)
        assert purchase_service._failure_rate == 0.5
        
        purchase_service.set_failure_rate(0.0)
        assert purchase_service._failure_rate == 0.0
    
    def test_failure_rate_bounded_to_valid_range(self, purchase_service):
        """Test that failure rate is bounded between 0 and 1"""
        purchase_service.set_failure_rate(-0.5)
        assert purchase_service._failure_rate == 0.0
        
        purchase_service.set_failure_rate(1.5)
        assert purchase_service._failure_rate == 1.0
    
    def test_failed_transaction_stored_in_history(self, purchase_service, mock_user_email):
        """Test that failed transactions are also stored"""
        purchase_service.set_failure_rate(1.0)
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        
        assert len(purchase_service.transaction_history) == 1
        assert purchase_service.transaction_history[0]['status'] == PurchaseStatus.FAILED


class TestTransactionRetrieval:
    """Test transaction lookup and retrieval"""
    
    def test_get_transaction_by_id(self, purchase_service, mock_user_email):
        """Test retrieving transaction by ID"""
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        transaction_id = result['transaction_id']
        
        retrieved = purchase_service.get_transaction(transaction_id)
        
        assert retrieved is not None
        assert retrieved['transaction_id'] == transaction_id
        assert retrieved == result
    
    def test_get_transaction_returns_none_for_invalid_id(self, purchase_service):
        """Test that invalid transaction ID returns None"""
        result = purchase_service.get_transaction("INVALID-ID")
        assert result is None
    
    def test_get_user_transactions(self, purchase_service):
        """Test retrieving all transactions for a user"""
        user1 = "user1@example.com"
        user2 = "user2@example.com"
        
        purchase_service.purchase_premium(user1, PurchasePlan.LIFETIME)
        purchase_service.purchase_premium(user2, PurchasePlan.LIFETIME)
        purchase_service.purchase_premium(user1, PurchasePlan.LIFETIME)
        
        user1_transactions = purchase_service.get_user_transactions(user1)
        user2_transactions = purchase_service.get_user_transactions(user2)
        
        assert len(user1_transactions) == 2
        assert len(user2_transactions) == 1
        assert all(t['user_email'] == user1 for t in user1_transactions)
        assert all(t['user_email'] == user2 for t in user2_transactions)
    
    def test_get_user_transactions_returns_empty_for_new_user(self, purchase_service):
        """Test that new user has no transactions"""
        transactions = purchase_service.get_user_transactions("newuser@example.com")
        assert transactions == []


class TestPurchaseCancellation:
    """Test purchase cancellation/refund functionality"""
    
    def test_cancel_successful_purchase(self, purchase_service, mock_user_email):
        """Test cancelling a successful purchase"""
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        transaction_id = result['transaction_id']
        
        cancelled = purchase_service.cancel_purchase(transaction_id)
        
        assert cancelled is True
        
        # Verify transaction marked as cancelled
        transaction = purchase_service.get_transaction(transaction_id)
        assert transaction['status'] == PurchaseStatus.CANCELLED
        assert 'cancelled_at' in transaction
    
    def test_cannot_cancel_invalid_transaction(self, purchase_service):
        """Test that invalid transaction cannot be cancelled"""
        result = purchase_service.cancel_purchase("INVALID-ID")
        assert result is False
    
    def test_cannot_cancel_failed_purchase(self, purchase_service, mock_user_email):
        """Test that failed purchase cannot be cancelled"""
        purchase_service.set_failure_rate(1.0)
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        transaction_id = result['transaction_id']
        
        cancelled = purchase_service.cancel_purchase(transaction_id)
        assert cancelled is False
    
    def test_cancel_updates_message(self, purchase_service, mock_user_email):
        """Test that cancellation updates message"""
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        transaction_id = result['transaction_id']
        
        purchase_service.cancel_purchase(transaction_id)
        
        transaction = purchase_service.get_transaction(transaction_id)
        assert 'refund' in transaction['message'].lower()


class TestTransactionDetails:
    """Test transaction data structure and details"""
    
    def test_transaction_has_all_required_fields(self, purchase_service, mock_user_email):
        """Test that transaction has all required fields"""
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        
        required_fields = [
            'status', 'transaction_id', 'user_email', 'plan', 
            'amount', 'currency', 'premium_until', 'purchased_at', 'message'
        ]
        
        for field in required_fields:
            assert field in result
    
    def test_purchased_at_is_recent(self, purchase_service, mock_user_email):
        """Test that purchased_at timestamp is recent"""
        before = datetime.now(timezone.utc)
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        after = datetime.now(timezone.utc)
        
        purchased_at = result['purchased_at']
        
        assert purchased_at >= before
        assert purchased_at <= after
    
    def test_transaction_id_format(self, purchase_service, mock_user_email):
        """Test that transaction ID has expected format"""
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        transaction_id = result['transaction_id']
        
        assert transaction_id.startswith('TXN-')
        assert len(transaction_id) > 10  # Should have timestamp and random suffix
    
    def test_currency_is_php(self, purchase_service, mock_user_email):
        """Test that currency is PHP"""
        result = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        assert result['currency'] == 'PHP'


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_multiple_purchases_same_user(self, purchase_service, mock_user_email):
        """Test that same user can make multiple purchases"""
        result1 = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        result2 = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME)
        
        assert result1['status'] == PurchaseStatus.SUCCESS
        assert result2['status'] == PurchaseStatus.SUCCESS
        assert result1['transaction_id'] != result2['transaction_id']
    
    def test_purchase_with_different_payment_methods(self, purchase_service, mock_user_email):
        """Test purchase with different payment method identifiers"""
        result1 = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME, "card_1")
        result2 = purchase_service.purchase_premium(mock_user_email, PurchasePlan.LIFETIME, "card_2")
        
        assert result1['status'] == PurchaseStatus.SUCCESS
        assert result2['status'] == PurchaseStatus.SUCCESS
    
    def test_plan_features_list_not_empty(self, purchase_service):
        """Test that all plans have features listed"""
        for plan in PurchasePlan:
            info = PurchaseService.get_plan_info(plan)
            assert len(info['features']) >= 4  # At least 4 features (watermark removed)

"""
Mock Purchase Service for Premium Upgrades
Simulates a payment API for upgrading users to premium
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from enum import Enum
import random


class PurchaseStatus(Enum):
    """Status of a purchase transaction"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    CANCELLED = "cancelled"


class PurchasePlan(Enum):
    """Available premium plans"""
    LIFETIME = "lifetime"


class PurchaseService:
    """Mock purchase service for premium upgrades"""
    
    # Pricing configuration (Philippine Pesos)
    PRICES = {
        PurchasePlan.LIFETIME: 5.00,
    }
    
    # Duration mapping
    DURATIONS = {
        PurchasePlan.LIFETIME: timedelta(days=36500),  # 100 years
    }
    
    def __init__(self, mock_mode: bool = True):
        """
        Initialize purchase service
        
        Args:
            mock_mode: If True, simulates successful purchases. If False, implements real payment logic.
        """
        self.mock_mode = mock_mode
        self.transaction_history = []
        self._failure_rate = 0.0  # For testing: 0.0 = always succeed, 1.0 = always fail
    
    def set_failure_rate(self, rate: float):
        """
        Set the failure rate for mock purchases (for testing)
        
        Args:
            rate: Float between 0.0 and 1.0
        """
        self._failure_rate = max(0.0, min(1.0, rate))
    
    def purchase_premium(
        self,
        user_email: str,
        plan: PurchasePlan,
        payment_method: str = "mock_card"
    ) -> Dict[str, Any]:
        """
        Process a premium purchase
        
        Args:
            user_email: Email of the user making the purchase
            plan: Premium plan being purchased
            payment_method: Payment method identifier
            
        Returns:
            Dictionary containing purchase result with keys:
                - status: PurchaseStatus
                - transaction_id: Unique transaction ID
                - premium_until: Datetime when premium expires
                - amount: Amount charged
                - plan: Plan purchased
                - message: Status message
        """
        # Generate transaction ID
        transaction_id = self._generate_transaction_id()
        
        # Get plan details
        amount = self.PRICES[plan]
        duration = self.DURATIONS[plan]
        
        # Simulate payment processing in mock mode
        if self.mock_mode:
            # Randomly fail based on failure rate (for testing)
            if random.random() < self._failure_rate:
                result = self._create_failed_transaction(
                    transaction_id, user_email, plan, amount,
                    "Payment declined (mock)"
                )
            else:
                result = self._create_successful_transaction(
                    transaction_id, user_email, plan, amount, duration
                )
        else:
            # In real mode, would integrate with actual payment gateway
            result = self._create_failed_transaction(
                transaction_id, user_email, plan, amount,
                "Real payment gateway not implemented"
            )
        
        # Store transaction
        self.transaction_history.append(result)
        
        return result
    
    def _create_successful_transaction(
        self,
        transaction_id: str,
        user_email: str,
        plan: PurchasePlan,
        amount: float,
        duration: timedelta
    ) -> Dict[str, Any]:
        """Create a successful transaction record"""
        premium_until = datetime.now(timezone.utc) + duration
        
        return {
            'status': PurchaseStatus.SUCCESS,
            'transaction_id': transaction_id,
            'user_email': user_email,
            'plan': plan.value,
            'amount': amount,
            'currency': 'PHP',
            'premium_until': premium_until,
            'purchased_at': datetime.now(timezone.utc),
            'message': f'Successfully purchased {plan.value} premium plan',
        }
    
    def _create_failed_transaction(
        self,
        transaction_id: str,
        user_email: str,
        plan: PurchasePlan,
        amount: float,
        reason: str
    ) -> Dict[str, Any]:
        """Create a failed transaction record"""
        return {
            'status': PurchaseStatus.FAILED,
            'transaction_id': transaction_id,
            'user_email': user_email,
            'plan': plan.value,
            'amount': amount,
            'currency': 'PHP',
            'premium_until': None,
            'purchased_at': datetime.now(timezone.utc),
            'message': f'Purchase failed: {reason}',
        }
    
    def _generate_transaction_id(self) -> str:
        """Generate a unique transaction ID"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        return f"TXN-{timestamp}-{random_suffix}"
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a transaction by ID
        
        Args:
            transaction_id: Transaction ID to look up
            
        Returns:
            Transaction dictionary or None if not found
        """
        for transaction in self.transaction_history:
            if transaction['transaction_id'] == transaction_id:
                return transaction
        return None
    
    def get_user_transactions(self, user_email: str) -> list[Dict[str, Any]]:
        """
        Get all transactions for a user
        
        Args:
            user_email: Email of the user
            
        Returns:
            List of transaction dictionaries
        """
        return [
            t for t in self.transaction_history
            if t['user_email'] == user_email
        ]
    
    def cancel_purchase(self, transaction_id: str) -> bool:
        """
        Cancel a purchase (refund)
        
        Args:
            transaction_id: Transaction to cancel
            
        Returns:
            True if cancelled successfully
        """
        transaction = self.get_transaction(transaction_id)
        
        if not transaction:
            return False
        
        if transaction['status'] != PurchaseStatus.SUCCESS:
            return False
        
        # Mark as cancelled
        transaction['status'] = PurchaseStatus.CANCELLED
        transaction['cancelled_at'] = datetime.now(timezone.utc)
        transaction['message'] = 'Purchase cancelled and refunded'
        
        return True
    
    @staticmethod
    def get_plan_info(plan: PurchasePlan) -> Dict[str, Any]:
        """
        Get information about a premium plan
        
        Args:
            plan: Plan to get info for
            
        Returns:
            Dictionary with plan details
        """
        plan_descriptions = {
            PurchasePlan.LIFETIME: "Lifetime Premium Access - One-time Payment",
        }
        
        plan_features = [
            "✓ Unlimited video arrangements",
            "✓ No advertisements",
            "✓ Direct YouTube upload",
            "✓ Priority support",
        ]
        
        return {
            'plan': plan.value,
            'price': PurchaseService.PRICES[plan],
            'currency': 'PHP',
            'duration_days': PurchaseService.DURATIONS[plan].days,
            'description': plan_descriptions[plan],
            'features': plan_features,
        }
    
    @staticmethod
    def get_all_plans() -> list[Dict[str, Any]]:
        """Get information about all available plans"""
        return [
            PurchaseService.get_plan_info(plan)
            for plan in PurchasePlan
        ]


# Global purchase service instance (singleton pattern)
_purchase_service_instance = None


def get_purchase_service(mock_mode: bool = True) -> PurchaseService:
    """
    Get the global purchase service instance
    
    Args:
        mock_mode: Whether to use mock mode (default: True)
        
    Returns:
        PurchaseService instance
    """
    global _purchase_service_instance
    
    if _purchase_service_instance is None:
        _purchase_service_instance = PurchaseService(mock_mode=mock_mode)
    
    return _purchase_service_instance


def reset_purchase_service():
    """Reset the global purchase service instance (mainly for testing)"""
    global _purchase_service_instance
    _purchase_service_instance = None


# Export commonly used items
__all__ = [
    'PurchaseService',
    'PurchaseStatus',
    'PurchasePlan',
    'get_purchase_service',
    'reset_purchase_service',
]

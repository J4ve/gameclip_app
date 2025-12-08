# Premium Purchase Testing Quick Reference

## Run All Purchase Tests
```bash
pytest tests/test_purchase_service.py tests/test_session_purchase.py -v
```

## Run Specific Test Classes

### Purchase Service Tests
```bash
# All purchase service tests (40 tests)
pytest tests/test_purchase_service.py -v

# Initialization tests
pytest tests/test_purchase_service.py::TestPurchaseServiceInitialization -v

# Plan configuration tests
pytest tests/test_purchase_service.py::TestPurchasePlans -v

# Successful purchase flow
pytest tests/test_purchase_service.py::TestSuccessfulPurchases -v

# Failed purchase scenarios
pytest tests/test_purchase_service.py::TestFailedPurchases -v
```

### Session Purchase Integration Tests
```bash
# All session purchase tests (21 tests)
pytest tests/test_session_purchase.py -v

# Basic purchase validation
pytest tests/test_session_purchase.py::TestPurchasePremiumBasics -v

# Successful purchase and role upgrade
pytest tests/test_session_purchase.py::TestSuccessfulPurchase -v
pytest tests/test_session_purchase.py::TestRoleUpgradeOnPurchase -v

# Firebase integration
pytest tests/test_session_purchase.py::TestFirebaseIntegration -v

# Premium feature verification
pytest tests/test_session_purchase.py::TestPremiumFeatures -v
```

## Key Test Scenarios

### ✅ Happy Path - Successful Purchase
```python
# test_successful_monthly_purchase
# Tests: Free user → Purchase monthly → Becomes premium
# Verifies: Role upgrade, premium status, transaction ID
```

### ✅ Premium Benefits Verification
```python
# test_unlimited_arrangements_after_purchase
# Tests: Merge limit check before/after purchase
# Verifies: Unlimited arrangements for premium

# test_no_ads_after_purchase  
# Tests: has_ads() before/after purchase
# Verifies: Ads disabled for premium
```

### ✅ Access Control
```python
# test_purchase_fails_when_not_logged_in
# Tests: Purchase without login → Fails
# Verifies: Authentication required

# test_purchase_fails_for_guest_user
# Tests: Guest user purchase → Blocked
# Verifies: Guests cannot purchase
```

### ✅ Error Handling
```python
# test_invalid_plan_returns_error
# Tests: Invalid plan name → Error response
# Verifies: Plan validation

# test_failed_purchase_doesnt_upgrade_role
# Tests: Failed payment → No role change
# Verifies: Transaction atomicity
```

### ✅ Firebase Integration
```python
# test_premium_until_synced_to_firebase
# Tests: Purchase → Firebase premium_until updated
# Verifies: Persistence layer sync

# test_purchase_works_without_firebase
# Tests: Firebase unavailable → Local success
# Verifies: Graceful degradation
```

## Quick Test Commands

### Fast Run (No Output)
```bash
pytest tests/test_purchase_service.py tests/test_session_purchase.py -q
```

### With Coverage
```bash
pytest tests/test_purchase_service.py tests/test_session_purchase.py --cov=src/access_control/purchase_service --cov=src/access_control/session --cov-report=term-missing
```

### Verbose with Detailed Output
```bash
pytest tests/test_purchase_service.py tests/test_session_purchase.py -vv -s
```

### Stop on First Failure
```bash
pytest tests/test_purchase_service.py tests/test_session_purchase.py -x
```

## Test Statistics

| Test File | Tests | Classes | Coverage |
|-----------|-------|---------|----------|
| test_purchase_service.py | 40 | 8 | Purchase API, Plans, Transactions |
| test_session_purchase.py | 21 | 8 | Session integration, Role upgrade, Firebase |
| **Total** | **61** | **16** | **100% Pass Rate** |

## Expected Test Output
```
tests/test_purchase_service.py ........................................  [ 65%]
tests/test_session_purchase.py .....................                    [100%]

61 passed, 18 warnings in 6.36s
```

## Common Issues & Solutions

### Issue: Import Error
```
ImportError: cannot import name 'get_purchase_service'
```
**Solution**: Ensure `src/access_control/purchase_service.py` exists

### Issue: Mock Patch Path Wrong
```
AttributeError: ... does not have the attribute 'get_purchase_service'
```
**Solution**: Use `@patch('access_control.purchase_service.get_purchase_service')`

### Issue: Firebase Warnings
```
UserWarning: Detected filter using positional arguments
```
**Solution**: These are warnings from Firebase SDK, not errors. Safe to ignore.

## Manual Testing in App

### Test Purchase Flow:
1. Launch app: `flet run src/main.py`
2. Login as free user
3. Add videos and proceed to upload screen
4. Click YouTube upload button
5. Premium dialog appears
6. Click "Upgrade to Premium"
7. Purchase dialog opens
8. Select plan (Monthly/Yearly/Lifetime)
9. Click "Purchase"
10. Verify success message
11. Verify upload button now enabled

### Verify Premium Features:
```python
from access_control.session import session_manager

# Check current status
print(f"Is Premium: {session_manager.is_premium()}")
print(f"Has Ads: {session_manager.has_ads()}")
print(f"Can Upload: {session_manager.can_upload()}")
print(f"Merge Limit: {session_manager.get_merge_limit()}")
```

## Debugging Tests

### Run Single Test with Print Output
```bash
pytest tests/test_session_purchase.py::TestSuccessfulPurchase::test_successful_monthly_purchase -v -s
```

### Run with Detailed Traceback
```bash
pytest tests/test_purchase_service.py -v --tb=long
```

### Run with PDB on Failure
```bash
pytest tests/test_session_purchase.py --pdb
```

## Test Data Validation

### Transaction Structure
```python
{
    'status': PurchaseStatus.SUCCESS,
    'transaction_id': 'TXN-20251209120000-123456',
    'user_email': 'user@test.com',
    'plan': 'monthly',
    'amount': 9.99,
    'currency': 'USD',
    'premium_until': datetime(...),
    'purchased_at': datetime(...),
    'message': 'Successfully purchased monthly premium plan'
}
```

### Plan Information
```python
{
    'plan': 'monthly',
    'price': 9.99,
    'currency': 'USD',
    'duration_days': 30,
    'description': '1 Month of Premium Access',
    'features': [...]
}
```

---

**Last Updated**: December 9, 2025  
**Test Suite Status**: ✅ All Passing  
**Total Tests**: 61

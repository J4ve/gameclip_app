# Testing Guide: Metadata Presets

## Quick Start

### Run Unit Tests (No Firebase Required)
```bash
pytest tests/test_metadata_presets.py -v -m "not integration"
```

**Expected Result:** 14 tests pass ✅

### Run All Tests (Requires Firebase)
```bash
pytest tests/test_metadata_presets.py -v
```

**Expected Result:** 16 tests (14 unit + 2 integration)

## Test Coverage

### Unit Tests (Mocked Firebase)

1. **Create Preset Tests**
   - ✅ Create preset successfully
   - ✅ Handle Firebase unavailable
   - ✅ Handle special characters and emojis

2. **Read Preset Tests**
   - ✅ Get user presets (multiple)
   - ✅ Get empty preset list
   - ✅ Get preset by ID
   - ✅ Handle preset not found
   - ✅ Handle Firebase unavailable

3. **Update Preset Tests**
   - ✅ Update preset successfully
   - ✅ Handle Firebase unavailable

4. **Delete Preset Tests**
   - ✅ Delete preset successfully
   - ✅ Handle Firebase unavailable

5. **Security Tests**
   - ✅ Multi-user isolation (users can't see each other's presets)

### Integration Tests (Real Firebase)

1. **Full CRUD Flow**
   - Create → Retrieve → Verify → Delete
   
2. **Update Flow**
   - Create → Update → Verify → Delete

## Prerequisites for Integration Tests

### 1. Firebase Configuration
- Ensure `configs/firebase-admin-key.json` exists
- Firebase project must be properly configured

### 2. Firestore Index
The integration tests require a composite index. If you see this error:
```
400 The query requires an index
```

**Solution:** Create the index following `docs/FIREBASE_INDEXES.md`

## Test Output Examples

### Successful Unit Tests
```
tests/test_metadata_presets.py::TestMetadataPresets::test_create_preset PASSED [  7%]
tests/test_metadata_presets.py::TestMetadataPresets::test_get_user_presets PASSED [ 14%]
...
============================================== 14 passed in 1.41s ==============================================
```

### Integration Test (Index Required)
```
tests/test_metadata_presets.py::TestMetadataPresetsIntegration::test_create_and_retrieve_preset_real_firebase SKIPPED
Reason: Firebase index not created yet. See docs/FIREBASE_INDEXES.md
```

### All Tests Passing
```
============================================== 16 passed in 3.21s ==============================================
```

## Manual Testing in UI

### Test Save Preset to Cloud

1. **Open Config Tab** in the application
2. **Fill in metadata template fields:**
   - Template Name: "Test Gaming"
   - Title: "Epic Gaming - {filename}"
   - Description: "Test description"
   - Tags: "gaming, test"
   - Visibility: "unlisted"
3. **Click "Save as Database Preset"**
4. **Expected:** Success message "Preset 'Test Gaming' saved to cloud!"

### Test Load Preset from Cloud

1. **Click "Load from Database"**
2. **Expected:** Dialog shows your saved presets
3. **Click "Load" on a preset**
4. **Expected:** Fields populate with preset data

### Test Delete Preset

1. **Click "Load from Database"**
2. **Click delete icon (🗑️) on a preset**
3. **Expected:** Success message and preset removed from list

## Troubleshooting

### Issue: "Firebase not available"
**Cause:** Firebase configuration missing or invalid  
**Solution:** Check `configs/firebase-admin-key.json` exists and is valid

### Issue: "The query requires an index"
**Cause:** Firestore composite index not created  
**Solution:** Follow `docs/FIREBASE_INDEXES.md` to create index

### Issue: "No user email found"
**Cause:** User not logged in  
**Solution:** Ensure user is authenticated with Google OAuth

### Issue: Tests fail with import errors
**Cause:** Dependencies not installed  
**Solution:** 
```bash
pip install pytest pytest-mock
```

## Continuous Integration

### GitHub Actions Example
```yaml
- name: Run Metadata Preset Tests
  run: |
    pytest tests/test_metadata_presets.py -v -m "not integration"
```

This skips integration tests in CI since they require Firebase credentials.

## Coverage Report

To generate coverage report:
```bash
pytest tests/test_metadata_presets.py --cov=src.access_control.firebase_service --cov-report=html
```

View report: `htmlcov/index.html`

## Test Data Cleanup

Integration tests automatically clean up test data:
- Presets created during tests are deleted in `finally` blocks
- No manual cleanup required

## Performance Testing

To test with multiple presets:
```python
# Create multiple test presets
for i in range(100):
    firebase.create_preset(
        f'test_user@example.com',
        {'name': f'Preset {i}', ...}
    )

# Measure retrieval time
import time
start = time.time()
presets = firebase.get_user_presets('test_user@example.com')
duration = time.time() - start
print(f"Retrieved {len(presets)} presets in {duration:.3f}s")
```

## Best Practices

1. **Always run unit tests first** - They're fast and catch most issues
2. **Use meaningful test data** - Makes debugging easier
3. **Check Firebase Console** - Verify data is stored correctly
4. **Clean up after manual tests** - Delete test presets in UI
5. **Run integration tests before deploy** - Ensures Firebase connectivity

## Quick Reference

| Command | Purpose |
|---------|---------|
| `pytest tests/test_metadata_presets.py -v` | Run all tests |
| `pytest tests/test_metadata_presets.py -v -m "not integration"` | Unit tests only |
| `pytest tests/test_metadata_presets.py -v -m "integration"` | Integration tests only |
| `pytest tests/test_metadata_presets.py -k "create"` | Run create-related tests |
| `pytest tests/test_metadata_presets.py --pdb` | Debug on failure |
| `pytest tests/test_metadata_presets.py -x` | Stop on first failure |

# Test Fixes - URL Converter Issue

## Problem
Tests fail with: `ValueError: Converter 'drf_format_suffix' is already registered`

This happens because Django REST Framework registers URL converters when routers are initialized, and when multiple tests run, it tries to register the same converter again.

## Solution Applied

1. **conftest.py fixture**: Automatically clears URL caches before/after each test
2. **setUp methods**: Additional cache clearing in test classes that use URL routing
3. **Settings**: `URL_FORMAT_OVERRIDE: None` in REST_FRAMEWORK settings to disable format suffixes

## If Tests Still Fail

If you still see converter registration errors, try:

1. **Run tests in isolation:**
   ```bash
   pytest credentials/tests/test_views.py::CredentialIssueViewTest::test_issue_credential_with_file -v
   ```

2. **Use Django's test runner instead:**
   ```bash
   python manage.py test credentials.tests.test_views.CredentialIssueViewTest.test_issue_credential_with_file
   ```

3. **Clear Python cache:**
   ```bash
   find . -type d -name __pycache__ -exec rm -r {} +
   find . -type f -name "*.pyc" -delete
   ```

4. **Run with fresh database:**
   ```bash
   pytest --create-db credentials/tests/ -v
   ```

## Alternative: Disable Format Suffixes Completely

If the issue persists, you can modify `blockproof_backend/settings.py` to completely disable format suffixes:

```python
REST_FRAMEWORK = {
    # ... other settings ...
    'URL_FORMAT_OVERRIDE': None,
}

# Also add this to prevent DRF from registering converters
import rest_framework.urls
# This prevents format suffix converter registration
```

But this is already set in the current settings.





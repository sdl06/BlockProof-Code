# Testing Guide

This document explains how to run tests for the BlockProof backend.

## Setup

1. **Install test dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure Django settings are configured:**
   - Make sure your `.env` file is set up (or use defaults)
   - Database will be created automatically for testing

## Running Tests

### Option 1: Using pytest (Recommended)

```bash
# Run all tests
pytest

# Run specific test file
pytest credentials/tests/test_document_service.py

# Run specific test
pytest credentials/tests/test_document_service.py::DocumentServiceTest::test_generate_file_hash

# Run with coverage
pytest --cov=credentials --cov-report=html
```

### Option 2: Using Django's test runner

```bash
python manage.py test credentials.tests
```

### Option 3: Using the test runner script

```bash
python run_tests.py
```

## Test Structure

Tests are organized in the `credentials/tests/` directory:

- `test_document_service.py` - Tests for file processing, hash generation, OCR integration
- `test_ocr_helpers.py` - Tests for OCR.space API helpers
- `test_views.py` - Tests for credential issuance endpoint
- `test_verification_views.py` - Tests for public verification endpoints
- `test_serializers.py` - Tests for API serializers and validation

## Test Coverage

Current test coverage includes:

✅ **Document Service:**
- File hash generation
- Credential fingerprint generation
- OCR integration (mocked)
- File storage

✅ **OCR Helpers:**
- OCR.space file upload
- OCR.space URL requests
- Error handling

✅ **Views:**
- Credential issuance with file upload
- Credential issuance without file
- Validation errors
- Blockchain/IPFS failure handling

✅ **Verification:**
- Valid credential verification
- Tampered document detection
- Revoked credential handling
- Expired credential handling
- Blockchain fallback

✅ **Serializers:**
- IPFS/URL field validation
- Credential issue request validation
- Optional field handling

## Mocking

Tests use mocks for:
- **Blockchain service** - Avoids actual blockchain calls
- **IPFS service** - Avoids actual IPFS uploads
- **OCR.space API** - Avoids actual API calls
- **File system** - Uses temporary files

## Continuous Integration

To run tests in CI/CD:

```bash
pytest --cov=credentials --cov-report=xml --junitxml=test-results.xml
```

## Troubleshooting

### Database errors
- Tests use a separate test database
- Run `python manage.py migrate` if needed

### Import errors
- Ensure you're in the `backend/` directory
- Check that `DJANGO_SETTINGS_MODULE` is set correctly

### Mock errors
- Ensure all external dependencies are properly mocked
- Check that test fixtures are set up correctly

## Adding New Tests

When adding new functionality:

1. Create test file in `credentials/tests/`
2. Follow naming convention: `test_*.py`
3. Use descriptive test names: `test_function_name_scenario`
4. Mock external dependencies
5. Test both success and failure cases
6. Test edge cases and validation

Example:
```python
def test_new_feature_success(self):
    """Test new feature with valid input."""
    # Arrange
    # Act
    # Assert
```








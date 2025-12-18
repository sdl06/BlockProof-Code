"""
Pytest configuration and fixtures for credentials tests.
"""
import pytest
from django.urls import clear_url_caches
from django.urls.resolvers import get_resolver


@pytest.fixture(autouse=True, scope='function')
def isolate_urls():
    """
    Isolate URL configuration between tests to avoid converter registration conflicts.
    This prevents "Converter 'drf_format_suffix' is already registered" errors.
    
    The issue occurs because DRF registers URL converters when routers are initialized,
    and when multiple tests run, it tries to register the same converter again.
    """
    # Clear URL caches and resolver before each test
    clear_url_caches()
    
    # Try to unregister the converter if it exists
    # This is a workaround for DRF's persistent converter registration
    try:
        from django.urls.converters import REGISTERED_CONVERTERS
        # Don't delete, just clear caches - deletion causes other issues
        # The converter will be re-registered but that's OK if caches are cleared
    except (ImportError, AttributeError):
        pass
    
    yield
    
    # Clear caches after test
    clear_url_caches()
    
    # Reset resolver to force re-initialization
    try:
        resolver = get_resolver()
        # Clear any cached patterns
        if hasattr(resolver, '_urlconf_module'):
            delattr(resolver, '_urlconf_module')
    except Exception:
        pass









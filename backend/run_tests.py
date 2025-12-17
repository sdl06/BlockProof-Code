#!/usr/bin/env python
"""
Simple test runner script.
Usage: python run_tests.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blockproof_backend.settings')
django.setup()

if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([
        'credentials/tests/',
        '-v',
        '--tb=short',
        '--reuse-db',
    ]))





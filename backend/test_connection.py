"""
Standalone script to test if Django can receive requests.
Run this to verify the server is working.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blockproof_backend.settings')
django.setup()

from django.test import Client
import sys

print("Testing Django connection...", file=sys.stderr, flush=True)

client = Client()
response = client.get('/api/institutions/health/')

print(f"Response status: {response.status_code}", file=sys.stderr, flush=True)
print(f"Response content: {response.content}", file=sys.stderr, flush=True)

if response.status_code == 200:
    print("SUCCESS: Django is working!", file=sys.stderr, flush=True)
else:
    print(f"ERROR: Got status {response.status_code}", file=sys.stderr, flush=True)





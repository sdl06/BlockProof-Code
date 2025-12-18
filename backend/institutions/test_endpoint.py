"""
Simple test endpoint to verify requests are reaching Django.
Add this to urls.py temporarily for debugging.
"""
from django.http import JsonResponse
import sys

def test_endpoint(request):
    """Simple test endpoint that always logs and returns success."""
    print(f"[TEST] Request received: {request.method} {request.path}", file=sys.stderr, flush=True)
    print(f"[TEST] Headers: {dict(request.headers)}", file=sys.stderr, flush=True)
    print(f"[TEST] META keys: {list(request.META.keys())[:10]}", file=sys.stderr, flush=True)
    return JsonResponse({'status': 'ok', 'message': 'Test endpoint reached'})





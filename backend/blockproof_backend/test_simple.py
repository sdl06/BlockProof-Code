"""
Simple test view to verify Django is working.
"""
from django.http import JsonResponse
import sys

def test_simple(request):
    print("=" * 60, file=sys.stderr, flush=True)
    print("[SIMPLE TEST] Request received!", file=sys.stderr, flush=True)
    print(f"[SIMPLE TEST] Path: {request.path}", file=sys.stderr, flush=True)
    print("=" * 60, file=sys.stderr, flush=True)
    return JsonResponse({'status': 'ok', 'message': 'Simple test works!'})




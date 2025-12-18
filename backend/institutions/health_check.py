"""
Health check endpoint that doesn't require authentication.
Use this to verify Django is receiving requests.
"""
from django.http import JsonResponse
import sys

def health_check(request):
    """Simple health check that always logs and returns success."""
    print("=" * 50, file=sys.stderr, flush=True)
    print(f"[HEALTH CHECK] Request received!", file=sys.stderr, flush=True)
    print(f"[HEALTH CHECK] Method: {request.method}", file=sys.stderr, flush=True)
    print(f"[HEALTH CHECK] Path: {request.path}", file=sys.stderr, flush=True)
    print(f"[HEALTH CHECK] Full path: {request.get_full_path()}", file=sys.stderr, flush=True)
    print(f"[HEALTH CHECK] META keys count: {len(request.META)}", file=sys.stderr, flush=True)
    if 'HTTP_AUTHORIZATION' in request.META:
        print(f"[HEALTH CHECK] Authorization header: PRESENT", file=sys.stderr, flush=True)
    else:
        print(f"[HEALTH CHECK] Authorization header: MISSING", file=sys.stderr, flush=True)
    print("=" * 50, file=sys.stderr, flush=True)
    
    return JsonResponse({
        'status': 'ok',
        'message': 'Health check endpoint reached',
        'method': request.method,
        'path': request.path
    })





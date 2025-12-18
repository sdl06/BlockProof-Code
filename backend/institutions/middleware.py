"""
Middleware to log all incoming requests for debugging.
"""
import logging
import sys

# Use print as well to ensure we see output even if logging is misconfigured
logger = logging.getLogger('institutions')

class RequestLoggingMiddleware:
    """
    Log all incoming requests to help debug authentication issues.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Force print to stderr so it shows in console
        print("=" * 60, file=sys.stderr, flush=True)
        print("RequestLoggingMiddleware INITIALIZED", file=sys.stderr, flush=True)
        print("=" * 60, file=sys.stderr, flush=True)

    def __call__(self, request):
        # Log request details - use both logger and print
        log_msg = (
            f"Request: {request.method} {request.path} | "
            f"User: {getattr(request, 'user', None)} | "
            f"Auth Header: {'Present' if 'HTTP_AUTHORIZATION' in request.META else 'Missing'}"
        )
        print(log_msg, file=sys.stderr, flush=True)
        logger.info(log_msg)
        
        if 'HTTP_AUTHORIZATION' in request.META:
            auth_header = request.META['HTTP_AUTHORIZATION']
            # Don't log the full credentials, just indicate Basic Auth is present
            if auth_header.startswith('Basic '):
                debug_msg = f"Basic Auth header present (length: {len(auth_header)})"
                print(debug_msg, file=sys.stderr, flush=True)
                logger.debug(debug_msg)
        else:
            print("NO AUTHORIZATION HEADER FOUND", file=sys.stderr, flush=True)
            print(f"Available headers: {list(request.META.keys())}", file=sys.stderr, flush=True)
        
        response = self.get_response(request)
        
        # Log user AFTER authentication (after get_response which processes all middleware)
        user_after = getattr(request, 'user', None)
        if user_after and hasattr(user_after, 'is_authenticated'):
            print(f"User AFTER auth: {user_after}, authenticated: {user_after.is_authenticated}", file=sys.stderr, flush=True)
        
        # Log response
        response_msg = f"Response: {request.method} {request.path} -> {response.status_code}"
        print(response_msg, file=sys.stderr, flush=True)
        logger.info(response_msg)
        
        return response




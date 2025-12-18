"""
Authentication for institution-level API access.
"""
from rest_framework import authentication, exceptions
from institutions.models import Institution
import logging

logger = logging.getLogger('credentials')


class InstitutionAPIKeyAuthentication(authentication.BaseAuthentication):
    """
    Simple API key authentication for institutions.
    Expects 'X-Institution-API-Key' header.
    """
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_INSTITUTION_API_KEY') or request.META.get('X-Institution-API-Key')
        
        if not api_key:
            return None  # No authentication attempted
        
        try:
            institution = Institution.objects.get(api_key=api_key, is_active=True)
            return (institution, None)  # (user, auth) tuple
        except Institution.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or inactive institution API key')
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise exceptions.AuthenticationFailed('Authentication failed')

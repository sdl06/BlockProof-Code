from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Institution
from .serializers import InstitutionSerializer, InstitutionRegistrationSerializer
import logging
import sys

logger = logging.getLogger(__name__)


class InstitutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for institutions.
    Note: 'register' is excluded from lookup to avoid conflicts with registration endpoint.
    """
    queryset = Institution.objects.filter(is_active=True)
    serializer_class = InstitutionSerializer
    lookup_field = 'address'
    lookup_value_regex = r'0x[a-fA-F0-9]{40}'  # Only match valid Ethereum addresses
    
    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Get or update the institution profile for the currently authenticated user.
        GET: Returns institution profile
        PATCH: Updates institution name and/or address
        """
        # Use print to ensure we see this even if logging fails
        print(f"[INSTITUTIONS] Received /me request: method={request.method}", file=sys.stderr, flush=True)
        print(f"[INSTITUTIONS] User: {request.user}, authenticated: {request.user.is_authenticated if request.user else False}", file=sys.stderr, flush=True)
        print(f"[INSTITUTIONS] Auth header in META: {'HTTP_AUTHORIZATION' in request.META}", file=sys.stderr, flush=True)
        
        # Debug authentication - try to manually decode Basic Auth
        if 'HTTP_AUTHORIZATION' in request.META:
            auth_header = request.META['HTTP_AUTHORIZATION']
            if auth_header.startswith('Basic '):
                import base64
                try:
                    encoded = auth_header.split(' ')[1]
                    decoded = base64.b64decode(encoded).decode('utf-8')
                    username_from_header, password_from_header = decoded.split(':', 1)
                    print(f"[INSTITUTIONS] Decoded Basic Auth - Username: {username_from_header}, Password length: {len(password_from_header)}", file=sys.stderr, flush=True)
                    
                    # Try to authenticate manually
                    from django.contrib.auth import authenticate
                    user = authenticate(request=request, username=username_from_header, password=password_from_header)
                    print(f"[INSTITUTIONS] Manual authenticate result: {user}", file=sys.stderr, flush=True)
                except Exception as e:
                    print(f"[INSTITUTIONS] Error decoding Basic Auth: {e}", file=sys.stderr, flush=True)
        
        # Debug authentication
        if hasattr(request, 'auth'):
            print(f"[INSTITUTIONS] Request.auth: {request.auth}", file=sys.stderr, flush=True)
        
        logger.info(f"Received /me request: method={request.method}, user={request.user}, authenticated={request.user.is_authenticated if request.user else False}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            print(f"[INSTITUTIONS] WARNING: Unauthenticated request to /me endpoint", file=sys.stderr, flush=True)
            print(f"[INSTITUTIONS] User type: {type(request.user)}", file=sys.stderr, flush=True)
            logger.warning(f"Unauthenticated request to /me endpoint")
            return Response(
                {'error': 'Authentication required. Please check your username and password. If you just registered, make sure you use the correct credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            institution = request.user.institution_profile
            if not institution:
                logger.warning(f"User {request.user.username} has no institution_profile")
                return Response(
                    {'error': 'User is not associated with an institution. Please ensure your account is linked to an institution.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            logger.info(f"Successfully retrieved institution profile for user {request.user.username}: {institution.name}")
            
            if request.method == 'PATCH':
                # Update institution name and/or address
                name = request.data.get('name')
                address = request.data.get('address')
                
                if name is not None:
                    institution.name = name
                
                if address is not None:
                    # Validate address format
                    from web3 import Web3
                    if not address.startswith('0x') or len(address) != 42:
                        return Response(
                            {'error': 'Invalid Ethereum address format'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    try:
                        Web3.to_checksum_address(address)
                    except Exception:
                        return Response(
                            {'error': 'Invalid Ethereum address format'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    institution.address = address.lower()
                
                import time
                institution.last_updated_at = int(time.time())
                institution.save()
            
            serializer = InstitutionSerializer(institution)
            return Response(serializer.data)
        except AttributeError:
            return Response(
                {'error': 'User is not associated with an institution'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['POST'])
@permission_classes([AllowAny])
def register_institution(request):
    """
    Register a new institution account.
    Creates both Django User and Institution records.
    """
    print(f"[REGISTER] Received registration request", file=sys.stderr, flush=True)
    print(f"[REGISTER] Data: {request.data}", file=sys.stderr, flush=True)
    
    serializer = InstitutionRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        print(f"[REGISTER] Validation errors: {serializer.errors}", file=sys.stderr, flush=True)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = serializer.save()
        print(f"[REGISTER] Successfully created institution: {result['institution_name']} at {result['institution_address']}", file=sys.stderr, flush=True)
        return Response({
            'message': 'Institution account created successfully',
            'username': result['username'],
            'institution_name': result['institution_name'],
            'institution_address': result['institution_address'],
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        print(f"[REGISTER] Error creating institution: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return Response(
            {'error': f'Failed to create institution account: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


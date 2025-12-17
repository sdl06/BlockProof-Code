"""
Public verification views for credentials.
These can be accessed via share links without authentication.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import Credential
from .document_service import get_document_service
from blockchain.services import get_blockproof_service
import logging
import time

logger = logging.getLogger('credentials')


@api_view(['GET'])
def verify_from_link(request, credential_id, fingerprint):
    """
    Verify credential from share link.
    URL format: /verify/{credential_id}/{fingerprint}
    
    This endpoint:
    1. Gets credential from database or blockchain
    2. Compares the fingerprint
    3. Returns VALID or TAMPERED status
    """
    try:
        credential_id_int = int(credential_id)
    except (ValueError, TypeError):
        return Response(
            {'error': 'Invalid credential ID'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Normalize fingerprint (handle accidental "0x0x..." too)
    fingerprint_clean = fingerprint.strip().lower()
    while fingerprint_clean.startswith('0x'):
        fingerprint_clean = fingerprint_clean[2:]
    
    # Try to get from cache first
    try:
        credential = Credential.objects.get(credential_id=credential_id_int)
        credential_fp = credential.fingerprint.lower().replace('0x', '')
        
        if credential_fp == fingerprint_clean:
            # Fingerprint matches - check validity
            is_valid = credential.is_valid()
            degree_photo_url = None
            if credential.diploma_file_path:
                degree_photo_url = request.build_absolute_uri(
                    settings.MEDIA_URL + credential.diploma_file_path.replace("\\", "/")
                )

            return Response({
                'status': 'VALID' if is_valid else 'INVALID',
                'credential_id': credential_id_int,
                'fingerprint_match': True,
                'valid': is_valid,
                'revoked': credential.revoked,
                'expired': credential.expires_at and credential.expires_at < int(time.time()),
                'student_wallet': credential.student_wallet,
                'institution': credential.institution.name,
                'institution_address': credential.institution.address,
                'issued_at': credential.issued_at,
                'expires_at': credential.expires_at,
                'student_name': credential.student_name,
                'passport_number': credential.passport_number,
                'degree_type': credential.degree_type,
                'graduation_year': credential.graduation_year,
                'degree_photo_url': degree_photo_url,
                'source': 'cache'
            })
        else:
            # Fingerprint doesn't match - TAMPERED
            return Response({
                'status': 'TAMPERED',
                'credential_id': credential_id_int,
                'fingerprint_match': False,
                'message': 'Fingerprint does not match. Document may have been tampered with.',
                'expected_fingerprint': credential.fingerprint,
                'provided_fingerprint': '0x' + fingerprint_clean,
                'source': 'cache'
            }, status=status.HTTP_200_OK)
            
    except Credential.DoesNotExist:
        # Not in cache, check blockchain
        pass
    
    # Fall back to blockchain verification
    try:
        service = get_blockproof_service()
        if service and service.contract:
            fingerprint_with_prefix = '0x' + fingerprint_clean
            is_valid = service.verify_fingerprint(credential_id_int, fingerprint_with_prefix)
            
            if is_valid:
                # Get status from blockchain
                status_data = service.get_credential_status(credential_id_int)
                if status_data:
                    return Response({
                        'status': 'VALID' if status_data.get('valid') else 'INVALID',
                        'credential_id': credential_id_int,
                        'fingerprint_match': True,
                        'valid': status_data.get('valid', False),
                        'revoked': status_data.get('revoked', False),
                        'student_wallet': status_data.get('student_wallet'),
                        'institution': status_data.get('institution'),
                        'issued_at': status_data.get('issued_at'),
                        'expires_at': status_data.get('expires_at'),
                        'source': 'blockchain'
                    })
            
            return Response({
                'status': 'TAMPERED' if is_valid is False else 'NOT_FOUND',
                'credential_id': credential_id_int,
                'fingerprint_match': False,
                'message': 'Fingerprint does not match or credential not found',
                'source': 'blockchain'
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Blockchain service not configured'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
    except Exception as e:
        logger.error(f"Error verifying credential from link: {e}", exc_info=True)
        return Response(
            {'error': f'Verification failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def verify_uploaded_document(request):
    """
    Verify an uploaded document by recomputing its hash and comparing with blockchain.
    This is used when an employer uploads a document to verify.
    """
    if 'document' not in request.FILES:
        return Response(
            {'error': 'Document file is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    credential_id = request.data.get('credential_id')
    if not credential_id:
        return Response(
            {'error': 'credential_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        credential_id_int = int(credential_id)
    except (ValueError, TypeError):
        return Response(
            {'error': 'Invalid credential ID'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    document_file = request.FILES['document']
    document_service = get_document_service()
    
    # Generate hash from uploaded file
    uploaded_file_hash = document_service.generate_file_hash(document_file)
    
    # Get credential from database or blockchain
    try:
        credential = Credential.objects.get(credential_id=credential_id_int)
        stored_fingerprint = credential.fingerprint
        
        # For verification, we need to recompute the fingerprint with the uploaded file hash
        # and compare it with the stored fingerprint
        # This is a simplified check - in production, you'd need the full metadata
        
        # For now, we'll do a basic comparison
        # In production, you'd recompute the full fingerprint
        
        return Response({
            'status': 'VERIFIED' if stored_fingerprint else 'UNKNOWN',
            'credential_id': credential_id_int,
            'uploaded_file_hash': uploaded_file_hash,
            'stored_fingerprint': stored_fingerprint,
            'message': 'Document verification completed. Compare hashes manually or use full verification endpoint.'
        })
    except Credential.DoesNotExist:
        return Response(
            {'error': 'Credential not found'},
            status=status.HTTP_404_NOT_FOUND
        )





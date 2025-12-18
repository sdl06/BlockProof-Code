"""
Credential API views.
Read operations use cached data, write operations interact with blockchain.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
from .models import Credential, StudentVerificationRequest
from .serializers import CredentialSerializer, CredentialIssueRequestSerializer, StudentVerificationRequestSerializer
from .ipfs_service import get_ipfs_service
from .document_service import get_document_service
from blockchain.services import get_blockproof_service
from institutions.models import Institution
import logging
import time
import json
from django.db.models import Q
from web3 import Web3

logger = logging.getLogger('credentials')

def _normalize_0x_hex(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return v
    # Remove multiple 0x prefixes if present (handles "0x0x...")
    while v.lower().startswith("0x"):
        v = v[2:]
    return "0x" + v.lower()

def _explorer_tx_url(chain_id: int, tx_hash: str) -> str:
    # Keep in sync with blockchain.views._explorer_tx_url, but avoid importing views here.
    base = None
    if chain_id == 1:
        base = "https://etherscan.io"
    elif chain_id == 11155111:
        base = "https://sepolia.etherscan.io"
    elif chain_id == 84532:
        base = "https://sepolia.basescan.org"
    elif chain_id == 8453:
        base = "https://basescan.org"
    if not base:
        return ""
    return f"{base}/tx/{tx_hash}"

def _derive_student_wallet(passport_number: str) -> str:
    """
    Toy-app embedded wallet: derive a deterministic address from passport number.
    This avoids asking the user for a wallet while still satisfying the contract.
    """
    pn = (passport_number or "").strip().upper()
    digest = Web3.keccak(text=pn)
    # web3 HexBytes.hex() may already include "0x" depending on version.
    tail_hex = digest[-20:].hex()
    if isinstance(tail_hex, str) and tail_hex.startswith("0x"):
        tail_hex = tail_hex[2:]
    addr_hex = "0x" + tail_hex
    return Web3.to_checksum_address(addr_hex)

class CredentialViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for credential operations.
    Read-only by default to minimize blockchain writes.
    """
    queryset = Credential.objects.all()
    serializer_class = CredentialSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()

        # Unified query (wallet OR passport)
        q = self.request.query_params.get('q')
        if q:
            q_clean = q.strip()
            if q_clean.lower().startswith('0x') and len(q_clean) == 42:
                queryset = queryset.filter(student_wallet__iexact=q_clean)
            else:
                queryset = queryset.filter(passport_number__iexact=q_clean)
        
        # Filter by student wallet
        student_wallet = self.request.query_params.get('student_wallet')
        if student_wallet:
            queryset = queryset.filter(student_wallet__iexact=student_wallet)

        # Filter by passport number
        passport_number = self.request.query_params.get('passport_number')
        if passport_number:
            queryset = queryset.filter(passport_number__iexact=passport_number)
        
        # Filter by institution
        institution = self.request.query_params.get('institution')
        if institution:
            queryset = queryset.filter(institution__address__iexact=institution)
        
        # Filter by fingerprint
        fingerprint = self.request.query_params.get('fingerprint')
        if fingerprint:
            queryset = queryset.filter(fingerprint__iexact=fingerprint)
        
        # Filter by validity
        valid_only = self.request.query_params.get('valid_only')
        if valid_only == 'true':
            # Filter in database query, not by converting to list
            # This preserves pagination and queryset functionality
            queryset = queryset.filter(revoked=False)
            # Note: expires_at filtering would need a custom filter or annotation
            # For now, we'll filter expired ones in Python if needed
            # But this is less efficient - consider using database-level filtering
        
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def issue(self, request):
        """
        Issue a new credential on-chain.
        This is a write operation and costs gas.
        Requires institution authentication.
        """
        # Verify user is linked to an institution
        try:
            institution = request.user.institution_profile
            if not institution:
                return Response(
                    {'error': 'User is not associated with an institution'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except AttributeError:
            return Response(
                {'error': 'User is not associated with an institution'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CredentialIssueRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        current_timestamp = int(time.time())

        service = get_blockproof_service()
        if not service or not getattr(service, "account", None):
            return Response(
                {"error": "Blockchain service not configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Use authenticated institution's address/name automatically
        authenticated_institution = institution
        institution_name = authenticated_institution.name or ""
        institution_address = authenticated_institution.address or ""

        # derive student wallet from passport number unless explicitly provided (back-compat)
        passport_number = (data.get("passport_number") or "").strip()
        student_wallet = (data.get("student_wallet") or "").strip() or _derive_student_wallet(passport_number)
        
        # Normalize institution address
        try:
            institution_address = str(institution_address).lower()
        except Exception:
            institution_address = institution_address.lower() if institution_address else authenticated_institution.address.lower()
        
        # Use authenticated institution or get/create by address
        if authenticated_institution.address.lower() == institution_address:
            institution = authenticated_institution
        else:
            institution, _ = Institution.objects.get_or_create(
                address=institution_address,
                defaults={
                    'name': institution_name or 'Unknown Institution',
                    'created_at': current_timestamp,
                    'last_updated_at': current_timestamp
                }
            )
            # Update name if provided
            if institution_name and institution.name != institution_name:
                institution.name = institution_name
                institution.last_updated_at = current_timestamp
                institution.save(update_fields=["name", "last_updated_at"])
        
        # Process diploma file if uploaded
        document_service = get_document_service()
        file_hash = None
        diploma_file_path = None
        holograph_check = None
        
        if 'diploma_file' in request.FILES:
            diploma_file = request.FILES['diploma_file']
            
            # Generate hash from file
            file_hash = document_service.generate_file_hash(diploma_file)
            
            # Check holograph/OCR (fraud detection)
            holograph_check = document_service.check_holograph_ocr(diploma_file)
            
            # Save file (we'll need credential_id, so we'll save after issuance)
            # For now, we'll save it temporarily and move it after we get the credential_id
        
        # Prepare credential metadata
        ipfs_service = get_ipfs_service()
        
        # Build metadata JSON with new fields
        metadata = {
            'institution_address': institution_address,
            'student_wallet': student_wallet,
            'student_name': data.get('student_name', ''),
            'passport_number': data.get('passport_number', ''),
            'degree_type': data.get('degree_type', ''),
            'graduation_year': data.get('graduation_year'),
            'issued_at': current_timestamp,
            'expires_at': data.get('expires_at', 0),
            'version': '1.0',
        }
        
        # Add file hash to metadata if available
        if file_hash:
            metadata['diploma_file_hash'] = file_hash
            metadata['holograph_check'] = holograph_check
        
        # Upload metadata to IPFS (or use provided URI)
        if data.get('metadata_uri'):
            metadata_uri = data['metadata_uri']
        else:
            metadata_uri = ipfs_service.upload_json(metadata)
            if not metadata_uri:
                return Response(
                    {'error': 'Failed to upload metadata to IPFS'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Create encrypted payload (for now, we'll create a JSON payload)
        # In production, this should be properly encrypted
        encrypted_payload = {
            'credential_data': metadata,
            'encrypted': False,  # In production, this should be True with actual encryption
            'note': 'This is a development payload. In production, use proper encryption.'
        }
        
        # Upload encrypted payload to IPFS (or use provided URI)
        if data.get('encrypted_payload_uri'):
            encrypted_payload_uri = data['encrypted_payload_uri']
        else:
            encrypted_payload_uri = ipfs_service.upload_json(encrypted_payload)
            if not encrypted_payload_uri:
                return Response(
                    {'error': 'Failed to upload encrypted payload to IPFS'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Generate fingerprint automatically (or use provided)
        if data.get('fingerprint'):
            fingerprint = data['fingerprint']
        else:
            # Use file hash if available, otherwise use metadata
            if file_hash:
                fingerprint = document_service.generate_credential_fingerprint(
                    file_hash=file_hash,
                    institution_address=institution_address,
                    student_wallet=student_wallet,
                    student_name=data.get('student_name', ''),
                    passport_number=data.get('passport_number', ''),
                    degree_type=data.get('degree_type', ''),
                    graduation_year=data.get('graduation_year'),
                    issued_at=current_timestamp
                )
            else:
                # Fallback to metadata-based fingerprint
                fingerprint_data = {
                    'institution_address': institution_address,
                    'student_wallet': student_wallet,
                    'student_name': data.get('student_name', ''),
                    'passport_number': data.get('passport_number', ''),
                    'degree_type': data.get('degree_type', ''),
                    'graduation_year': data.get('graduation_year'),
                    'metadata_uri': metadata_uri,
                    'issued_at': current_timestamp,
                }
                fingerprint = ipfs_service.generate_fingerprint(fingerprint_data)

        fingerprint = _normalize_0x_hex(fingerprint)
        
        tx_hash = service.issue_credential(
            institution=institution_address,
            student_wallet=student_wallet,
            fingerprint=fingerprint,
            metadata_uri=metadata_uri,
            encrypted_payload_uri=encrypted_payload_uri,
            expires_at=data.get('expires_at', 0),
            institution_name=institution_name or institution.name,
        )
        
        if not tx_hash:
            return Response(
                {'error': 'Failed to issue credential on blockchain'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Try to resolve credential_id immediately (toy-app friendly).
        credential_id = None
        degree_photo_url = None
        try:
            receipt = service.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120, poll_latency=2)
            if getattr(receipt, "status", 0) != 1:
                chain_id = int(service.w3.eth.chain_id)
                return Response(
                    {
                        "error": "Transaction reverted (contract execution failed).",
                        "transaction_hash": tx_hash,
                        "chain_id": chain_id,
                        "explorer_url": _explorer_tx_url(chain_id, tx_hash),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            events = []
            if service.contract and hasattr(service.contract.events, "CredentialIssued"):
                events = service.contract.events.CredentialIssued().process_receipt(receipt)
            if events:
                credential_id = int(events[0].get("args", {}).get("credentialId"))
        except Exception as e:
            logger.warning(f"Could not resolve credential_id from tx receipt: {e}")

        # Save diploma file now that we may have a real credential_id
        if credential_id and 'diploma_file' in request.FILES and file_hash:
            try:
                diploma_file = request.FILES['diploma_file']
                diploma_file_path = document_service.save_diploma_file(diploma_file, credential_id)
                logger.info(f"Saved diploma file to: {diploma_file_path}")
                degree_photo_url = request.build_absolute_uri(settings.MEDIA_URL + diploma_file_path.replace("\\", "/"))
            except Exception as e:
                logger.error(f"Error saving diploma file: {e}", exc_info=True)
                diploma_file_path = None
        else:
            diploma_file_path = None
        
        # Generate share link (localhost:8080)
        # Format: http://localhost:8080/verify/{credential_id}/{fingerprint}
        # Note: credential_id will be available after event indexing
        share_link_base = f"http://localhost:8080/verify"
        
        # If resolved, persist a local cache record immediately (so verification + search work right away).
        if credential_id:
            try:
                status_data = service.get_credential_status(credential_id) or {}
                issued_at = int(status_data.get("issued_at") or current_timestamp)
                expires_at = status_data.get("expires_at")
                revoked = bool(status_data.get("revoked", False))
            except Exception:
                issued_at = current_timestamp
                expires_at = data.get('expires_at', 0)
                revoked = False

            Credential.objects.update_or_create(
                credential_id=credential_id,
                defaults={
                    "student_wallet": student_wallet,
                    "institution": institution,
                    "fingerprint": fingerprint,
                    "metadata_uri": metadata_uri,
                    "encrypted_payload_uri": encrypted_payload_uri,
                    "issued_at": issued_at,
                    "expires_at": expires_at or None,
                    "revoked": revoked,
                    "student_name": data.get("student_name", ""),
                    "passport_number": data.get("passport_number", ""),
                    "degree_type": data.get("degree_type", ""),
                    "graduation_year": data.get("graduation_year"),
                    "diploma_file_hash": file_hash,
                    "diploma_file_path": diploma_file_path,
                    "transaction_hash": tx_hash,
                },
            )

        # Return the transaction hash and generated values for reference
        response_data = {
            'transaction_hash': tx_hash,
            'credential_id': credential_id,
            'fingerprint': fingerprint,
            'metadata_uri': metadata_uri,
            'encrypted_payload_uri': encrypted_payload_uri,
            'file_hash': file_hash,
            'holograph_check': holograph_check,
            'share_link': f"{share_link_base}/{credential_id}/{fingerprint}" if credential_id else None,
            'share_link_template': f"{share_link_base}/{{credential_id}}/{fingerprint}",
            'degree_photo_url': degree_photo_url,
            'chain_id': getattr(getattr(service, "w3", None), "eth", None).chain_id if getattr(service, "w3", None) else getattr(service, "chain_id", None),
            'message': 'Credential issuance transaction submitted. It will appear after event indexing. Use the fingerprint to generate share link once credential_id is available.'
        }

        return Response(
            response_data,
            status=status.HTTP_201_CREATED if credential_id else status.HTTP_202_ACCEPTED
        )
    
    @action(detail=False, methods=['get'])
    def share_link(self, request):
        """
        Generate share link for a credential.
        Returns a URL that can be used to verify the credential.
        """
        credential_id = request.query_params.get('credential_id')
        fingerprint = request.query_params.get('fingerprint')
        
        if not credential_id or not fingerprint:
            return Response(
                {'error': 'credential_id and fingerprint are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate share link
        share_link = f"http://localhost:8080/verify/{credential_id}/{fingerprint}"
        
        return Response({
            'share_link': share_link,
            'credential_id': credential_id,
            'fingerprint': fingerprint,
        })
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """
        Revoke a credential on-chain.
        This is a write operation and costs gas.
        """
        credential = get_object_or_404(Credential, credential_id=pk)
        reason = request.data.get('reason', '')
        
        # Hash the reason
        from web3 import Web3
        reason_hash = Web3.keccak(text=reason).hex()
        
        # Revoke on blockchain
        service = get_blockproof_service()
        tx_hash = service.revoke_credential(credential.credential_id, reason_hash)
        
        if not tx_hash:
            return Response(
                {'error': 'Failed to revoke credential on blockchain'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'transaction_hash': tx_hash,
            'message': 'Revocation transaction submitted. It will be processed by the event indexer.'
        }, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # Public endpoint for students
def student_verify(request):
    """
    Student-initiated verification request.
    Steps:
    1. Student submits name, degree, graduation date, passport, wallet, diploma file
    2. System performs strict hologram OCR verification
    3. If verified, credential is automatically issued on-chain
    4. Student receives share link + QR code
    """
    serializer = StudentVerificationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Check if diploma file is provided
    if 'diploma_file' not in request.FILES:
        return Response(
            {'error': 'Diploma file is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    diploma_file = request.FILES['diploma_file']
    document_service = get_document_service()
    
    # Generate file hash
    file_hash = document_service.generate_file_hash(diploma_file)
    
    # STRICT hologram OCR verification
    hologram_check = None
    hologram_verified = False
    try:
        hologram_check = document_service.check_holograph_ocr(diploma_file, strict=True)
        hologram_verified = hologram_check.get('verified', False) if hologram_check else False
    except ValueError as e:
        # OCR verification failed - reject the request
        warnings = hologram_check.get('warnings', []) if hologram_check else []
        return Response(
            {
                'error': 'Document verification failed',
                'message': str(e),
                'hologram_check': {
                    'verified': False,
                    'warnings': warnings
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error during hologram OCR check: {e}", exc_info=True)
        return Response(
            {'error': 'Document verification error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    if not hologram_check or not hologram_check.get('verified', False):
        return Response(
            {
                'error': 'Document verification failed',
                'message': 'Hologram OCR could not verify document authenticity',
                'hologram_check': hologram_check or {'verified': False, 'warnings': []}
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create institution (use default backend account as institution)
    service = get_blockproof_service()
    if not service or not getattr(service, "account", None):
        return Response(
            {"error": "Blockchain service not configured"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    
    # Default to backend account as institution (students don't specify institution)
    institution_address = service.account.address
    institution_name = 'Verified Institution'  # Default name
    
    current_timestamp = int(time.time())
    institution, _ = Institution.objects.get_or_create(
        address=institution_address.lower(),
        defaults={
            'name': institution_name,
            'created_at': current_timestamp,
            'last_updated_at': current_timestamp
        }
    )
    
    # Create verification request record
    verification_request = StudentVerificationRequest.objects.create(
        student_name=data['student_name'],
        passport_number=data['passport_number'],
        student_wallet=data['student_wallet'],
        degree_type=data['degree_type'],
        graduation_date=data['graduation_date'],
        institution=institution,
        diploma_file=diploma_file,
        diploma_file_hash=file_hash,
        status=StudentVerificationRequest.STATUS_VERIFYING,
        hologram_ocr_result=hologram_check,
        hologram_verified=True,
    )
    
    # Auto-issue credential since OCR passed
    try:
        # Prepare metadata
        ipfs_service = get_ipfs_service()
        # Handle graduation_date (could be Date object or string)
        grad_date = data['graduation_date']
        if hasattr(grad_date, 'year'):
            graduation_year = grad_date.year
        elif isinstance(grad_date, str):
            graduation_year = int(grad_date.split('-')[0])
        else:
            graduation_year = None
        
        metadata = {
            'institution_address': institution_address,
            'student_wallet': data['student_wallet'],
            'student_name': data['student_name'],
            'passport_number': data['passport_number'],
            'degree_type': data['degree_type'],
            'graduation_year': graduation_year,
            'issued_at': current_timestamp,
            'expires_at': 0,
            'version': '1.0',
        }
        
        metadata['diploma_file_hash'] = file_hash
        metadata['hologram_check'] = hologram_check
        
        # Upload to IPFS
        metadata_uri = ipfs_service.upload_json(metadata)
        if not metadata_uri:
            verification_request.status = StudentVerificationRequest.STATUS_REJECTED
            verification_request.rejection_reason = 'Failed to upload metadata to IPFS'
            verification_request.save()
            return Response(
                {'error': 'Failed to upload metadata to IPFS'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        encrypted_payload = {
            'credential_data': metadata,
            'encrypted': False,
            'note': 'This is a development payload. In production, use proper encryption.'
        }
        encrypted_payload_uri = ipfs_service.upload_json(encrypted_payload)
        if not encrypted_payload_uri:
            verification_request.status = StudentVerificationRequest.STATUS_REJECTED
            verification_request.rejection_reason = 'Failed to upload encrypted payload to IPFS'
            verification_request.save()
            return Response(
                {'error': 'Failed to upload encrypted payload to IPFS'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Generate fingerprint
        fingerprint = document_service.generate_credential_fingerprint(
            file_hash=file_hash,
            institution_address=institution_address,
            student_wallet=data['student_wallet'],
            student_name=data['student_name'],
            passport_number=data['passport_number'],
            degree_type=data['degree_type'],
            graduation_year=graduation_year,
            issued_at=current_timestamp
        )
        fingerprint = _normalize_0x_hex(fingerprint)
        
        # Issue on blockchain
        tx_hash = service.issue_credential(
            institution=institution_address,
            student_wallet=data['student_wallet'],
            fingerprint=fingerprint,
            metadata_uri=metadata_uri,
            encrypted_payload_uri=encrypted_payload_uri,
            expires_at=0,
            institution_name=institution_name
        )
        
        if not tx_hash:
            verification_request.status = StudentVerificationRequest.STATUS_REJECTED
            verification_request.rejection_reason = 'Failed to issue credential on blockchain'
            verification_request.save()
            return Response(
                {'error': 'Failed to issue credential on blockchain'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Wait for receipt and get credential_id
        credential_id = None
        try:
            receipt = service.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120, poll_latency=2)
            if getattr(receipt, "status", 0) != 1:
                verification_request.status = StudentVerificationRequest.STATUS_REJECTED
                verification_request.rejection_reason = 'Transaction reverted'
                verification_request.save()
                return Response(
                    {'error': 'Transaction reverted', 'transaction_hash': tx_hash},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            events = []
            if service.contract and hasattr(service.contract.events, "CredentialIssued"):
                events = service.contract.events.CredentialIssued().process_receipt(receipt)
            if events:
                credential_id = int(events[0].get("args", {}).get("credentialId"))
        except Exception as e:
            logger.warning(f"Could not resolve credential_id from tx receipt: {e}")
        
        # Save diploma file
        diploma_file_path = None
        degree_photo_url = None
        if credential_id:
            try:
                diploma_file_path = document_service.save_diploma_file(diploma_file, credential_id)
                degree_photo_url = request.build_absolute_uri(settings.MEDIA_URL + diploma_file_path.replace("\\", "/"))
            except Exception as e:
                logger.error(f"Error saving diploma file: {e}", exc_info=True)
        
        # Create credential record
        if credential_id:
            try:
                status_data = service.get_credential_status(credential_id) or {}
                issued_at = int(status_data.get("issued_at") or current_timestamp)
                expires_at = status_data.get("expires_at")
                revoked = bool(status_data.get("revoked", False))
            except Exception:
                issued_at = current_timestamp
                expires_at = 0
                revoked = False
            
            credential = Credential.objects.update_or_create(
                credential_id=credential_id,
                defaults={
                    "student_wallet": data["student_wallet"],
                    "institution": institution,
                    "fingerprint": fingerprint,
                    "metadata_uri": metadata_uri,
                    "encrypted_payload_uri": encrypted_payload_uri,
                    "issued_at": issued_at,
                    "expires_at": expires_at or None,
                    "revoked": revoked,
                    "student_name": data["student_name"],
                    "passport_number": data["passport_number"],
                    "degree_type": data["degree_type"],
                    "graduation_year": graduation_year,
                    "diploma_file_hash": file_hash,
                    "diploma_file_path": diploma_file_path,
                    "transaction_hash": tx_hash,
                },
            )[0]
            
            verification_request.credential = credential
            verification_request.status = StudentVerificationRequest.STATUS_APPROVED
            verification_request.verified_at = timezone.now()
            
            # Generate share link
            share_link = f"http://localhost:8080/verify/{credential_id}/{fingerprint}"
            verification_request.share_link = share_link
            verification_request.save()
            
            return Response({
                'status': 'approved',
                'credential_id': credential_id,
                'transaction_hash': tx_hash,
                'fingerprint': fingerprint,
                'share_link': share_link,
                'degree_photo_url': degree_photo_url,
                'message': 'Document verified and credential issued successfully'
            }, status=status.HTTP_201_CREATED)
        else:
            # Credential issued but ID not resolved yet
            verification_request.status = StudentVerificationRequest.STATUS_APPROVED
            verification_request.save()
            return Response({
                'status': 'approved',
                'transaction_hash': tx_hash,
                'fingerprint': fingerprint,
                'message': 'Document verified and credential issued. Credential ID will be available after event indexing.'
            }, status=status.HTTP_202_ACCEPTED)
            
    except Exception as e:
        logger.error(f"Error issuing credential after verification: {e}", exc_info=True)
        verification_request.status = StudentVerificationRequest.STATUS_REJECTED
        verification_request.rejection_reason = f'Error during credential issuance: {str(e)}'
        verification_request.save()
        return Response(
            {'error': 'Failed to issue credential', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


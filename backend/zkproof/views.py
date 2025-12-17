"""
Zero-Knowledge Proof API views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import ZKProof, ZKProofVerification, ZKCircuit
from .serializers import (
    ZKProofSerializer,
    ZKProofVerificationSerializer,
    ZKProofGenerateRequestSerializer,
    ZKProofVerifyRequestSerializer,
    ZKCircuitSerializer
)
from .services import get_zkproof_service
from credentials.models import Credential
import time
import logging

logger = logging.getLogger('zkproof')


class ZKProofViewSet(viewsets.ModelViewSet):
    """
    ViewSet for zero-knowledge proof operations.
    """
    queryset = ZKProof.objects.all()
    serializer_class = ZKProofSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by credential
        credential_id = self.request.query_params.get('credential_id')
        if credential_id:
            queryset = queryset.filter(credential_id=credential_id)
        
        # Filter by proof type
        proof_type = self.request.query_params.get('proof_type')
        if proof_type:
            queryset = queryset.filter(proof_type=proof_type)
        
        # Filter by validity
        is_valid = self.request.query_params.get('is_valid')
        if is_valid is not None:
            queryset = queryset.filter(is_valid=is_valid.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate a new zero-knowledge proof for a credential.
        """
        serializer = ZKProofGenerateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        credential_id = data['credential_id']
        proof_type = data.get('proof_type', 'credential_validity')
        
        try:
            credential = Credential.objects.get(credential_id=credential_id)
        except Credential.DoesNotExist:
            return Response(
                {'error': f'Credential {credential_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate proof
        zkproof_service = get_zkproof_service()
        
        try:
            if proof_type == 'credential_validity':
                proof_data = zkproof_service.generate_credential_validity_proof(
                    credential_id=credential.credential_id,
                    fingerprint=credential.fingerprint,
                    student_wallet=credential.student_wallet,
                    institution=credential.institution.address,
                    secret_data=data.get('secret_data')
                )
            elif proof_type == 'selective_disclosure':
                # This would need credential metadata
                return Response(
                    {'error': 'Selective disclosure requires credential metadata'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {'error': f'Proof type {proof_type} not yet implemented'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save proof to database
            zkproof, created = ZKProof.objects.update_or_create(
                credential=credential,
                proof_type=proof_type,
                defaults={
                    'proof_data': proof_data,
                    'public_inputs': proof_data.get('public_inputs', {}),
                    'circuit_hash': proof_data.get('circuit_hash', 'commitment_v1'),
                    'is_valid': True,
                }
            )
            
            return Response(
                ZKProofSerializer(zkproof).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error generating proof: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Verify a zero-knowledge proof.
        """
        zkproof = get_object_or_404(ZKProof, pk=pk)
        expected_fingerprint = request.data.get('expected_fingerprint')
        
        zkproof_service = get_zkproof_service()
        start_time = time.time()
        
        try:
            is_valid, error_message = zkproof_service.verify_credential_validity_proof(
                proof=zkproof.proof_data,
                expected_fingerprint=expected_fingerprint
            )
            
            verification_time = time.time() - start_time
            
            # Record verification
            verification = ZKProofVerification.objects.create(
                proof=zkproof,
                verifier_address=request.data.get('verifier_address'),
                verification_result=is_valid,
                verification_time=verification_time,
                error_message=error_message,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT'),
            )
            
            # Update proof if verified
            if is_valid and not zkproof.verified_at:
                from django.utils import timezone
                zkproof.verified_at = timezone.now()
                zkproof.save()
            
            return Response({
                'valid': is_valid,
                'verification_time': verification_time,
                'error': error_message,
                'verification_id': verification.id,
            })
        except Exception as e:
            logger.error(f"Error verifying proof: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def verify_raw(self, request):
        """
        Verify a proof without storing it in database (for external proofs).
        """
        serializer = ZKProofVerifyRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        proof_data = data.get('proof_data')
        
        if not proof_data:
            return Response(
                {'error': 'proof_data is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        zkproof_service = get_zkproof_service()
        start_time = time.time()
        
        try:
            is_valid, error_message = zkproof_service.verify_credential_validity_proof(
                proof=proof_data,
                expected_fingerprint=data.get('expected_fingerprint')
            )
            
            verification_time = time.time() - start_time
            
            return Response({
                'valid': is_valid,
                'verification_time': verification_time,
                'error': error_message,
            })
        except Exception as e:
            logger.error(f"Error verifying raw proof: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ZKCircuitViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing zk-SNARK circuits.
    """
    queryset = ZKCircuit.objects.filter(is_active=True)
    serializer_class = ZKCircuitSerializer


@api_view(['GET'])
def zkproof_status(request):
    """
    Health check endpoint for zkproof service.
    """
    zkproof_service = get_zkproof_service()
    
    return Response({
        'enabled': zkproof_service.enabled,
        'circuit_path': zkproof_service.circuit_path,
        'artifacts_path': zkproof_service.artifacts_path,
        'status': 'operational' if zkproof_service.enabled else 'disabled',
    })











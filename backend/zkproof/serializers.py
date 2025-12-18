from rest_framework import serializers
from .models import ZKProof, ZKProofVerification, ZKCircuit
from credentials.serializers import CredentialSerializer


class ZKProofSerializer(serializers.ModelSerializer):
    credential = CredentialSerializer(read_only=True)
    credential_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = ZKProof
        fields = [
            'id',
            'credential',
            'credential_id',
            'proof_type',
            'proof_data',
            'proof_ipfs_hash',
            'public_inputs',
            'circuit_hash',
            'verification_key_ipfs',
            'is_valid',
            'verified_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'verified_at']


class ZKProofVerificationSerializer(serializers.ModelSerializer):
    proof = ZKProofSerializer(read_only=True)
    
    class Meta:
        model = ZKProofVerification
        fields = [
            'id',
            'proof',
            'verifier_address',
            'verification_result',
            'verification_time',
            'error_message',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ZKProofGenerateRequestSerializer(serializers.Serializer):
    """Serializer for generating a new zkproof."""
    credential_id = serializers.IntegerField()
    proof_type = serializers.ChoiceField(
        choices=['credential_validity', 'selective_disclosure', 'range_proof', 'membership_proof'],
        default='credential_validity'
    )
    secret_data = serializers.DictField(required=False, allow_null=True)
    disclosed_fields = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class ZKProofVerifyRequestSerializer(serializers.Serializer):
    """Serializer for verifying a zkproof."""
    proof_id = serializers.IntegerField(required=False)
    proof_data = serializers.DictField(required=False)
    expected_fingerprint = serializers.CharField(required=False, allow_blank=True)


class ZKCircuitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZKCircuit
        fields = [
            'id',
            'name',
            'description',
            'circuit_type',
            'circuit_hash',
            'verification_key_ipfs',
            'is_active',
            'version',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'circuit_hash', 'created_at', 'updated_at']















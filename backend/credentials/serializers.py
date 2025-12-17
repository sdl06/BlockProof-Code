from rest_framework import serializers
from .models import Credential
from institutions.serializers import InstitutionSerializer
import re
from django.core.files.uploadedfile import UploadedFile


class IPFSOrURLField(serializers.CharField):
    """
    Field that accepts both IPFS URIs (ipfs://...) and standard URLs (http://, https://).
    """
    def __init__(self, **kwargs):
        kwargs.setdefault('max_length', 500)
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        
        # Check if it's an IPFS URI
        if value.startswith('ipfs://'):
            return value
        
        # Check if it's a standard URL (http:// or https://)
        if value.startswith('http://') or value.startswith('https://'):
            return value
        
        # If neither, raise validation error
        raise serializers.ValidationError(
            'Must be a valid URL (http://, https://) or IPFS URI (ipfs://)'
        )


class CredentialSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = Credential
        fields = [
            'credential_id',
            'student_wallet',
            'institution',
            'fingerprint',
            'metadata_uri',
            'encrypted_payload_uri',
            'issued_at',
            'expires_at',
            'revoked',
            'revoked_at',
            'revocation_reason_hash',
            'student_name',
            'passport_number',
            'degree_type',
            'graduation_year',
            'diploma_file_hash',
            'diploma_file_path',
            'transaction_hash',
            'is_valid',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['credential_id', 'created_at', 'updated_at']
    
    def get_is_valid(self, obj):
        return obj.is_valid()


class CredentialIssueRequestSerializer(serializers.Serializer):
    """Serializer for issuing new credentials."""
    institution_address = serializers.CharField(max_length=42)
    institution_name = serializers.CharField(max_length=200)
    # Student wallet is no longer user-supplied (we derive it from passport number for the toy app)
    student_wallet = serializers.CharField(max_length=42, required=False, allow_blank=True)
    
    # New fields for credential metadata
    student_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    passport_number = serializers.CharField(max_length=50)
    degree_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    graduation_year = serializers.IntegerField(required=False, allow_null=True)
    
    # Diploma file upload (PDF or image)
    diploma_file = serializers.FileField(required=False, allow_null=True)
    
    # Optional: if provided, will be used; otherwise auto-generated
    fingerprint = serializers.CharField(max_length=66, required=False, allow_blank=True)
    metadata_uri = IPFSOrURLField(required=False, allow_blank=True)
    encrypted_payload_uri = IPFSOrURLField(required=False, allow_blank=True)
    
    expires_at = serializers.IntegerField(required=False, allow_null=True)


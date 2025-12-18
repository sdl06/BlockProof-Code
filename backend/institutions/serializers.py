from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Institution
from web3 import Web3
import time


class InstitutionSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    api_key = serializers.SerializerMethodField()
    
    class Meta:
        model = Institution
        fields = [
            'address',
            'name',
            'is_active',
            'created_at',
            'last_updated_at',
            'username',
            'api_key',
        ]
    
    def get_username(self, obj):
        """Get the username of the linked user."""
        if obj.user:
            return obj.user.username
        return None
    
    def get_api_key(self, obj):
        """Get the API key, generating it if it doesn't exist."""
        if not obj.api_key:
            obj.generate_api_key()
        return obj.api_key


class InstitutionRegistrationSerializer(serializers.Serializer):
    """Serializer for institution registration."""
    university_name = serializers.CharField(max_length=200, required=True)
    username = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(max_length=128, write_only=True, required=True, min_length=6)
    account_address = serializers.CharField(max_length=42, required=True)
    
    def validate_account_address(self, value):
        """Validate Ethereum address format."""
        if not value.startswith('0x'):
            raise serializers.ValidationError("Account address must start with '0x'")
        if len(value) != 42:
            raise serializers.ValidationError("Account address must be 42 characters (including 0x)")
        try:
            # Validate checksum address
            Web3.to_checksum_address(value)
        except Exception:
            raise serializers.ValidationError("Invalid Ethereum address format")
        return value.lower()
    
    def validate_username(self, value):
        """Check if username already exists."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def create(self, validated_data):
        """Create User and Institution."""
        username = validated_data['username']
        password = validated_data['password']
        university_name = validated_data['university_name']
        account_address = validated_data['account_address']
        
        # Create Django User
        user = User.objects.create_user(
            username=username,
            password=password,
            email=f"{username}@institution.local"  # Placeholder email
        )
        
        # Create Institution linked to User
        current_timestamp = int(time.time())
        institution = Institution.objects.create(
            address=account_address,
            name=university_name,
            user=user,
            is_active=True,
            created_at=current_timestamp,
            last_updated_at=current_timestamp
        )
        
        return {
            'user_id': user.id,
            'institution_id': institution.id,
            'username': username,
            'institution_name': university_name,
            'institution_address': account_address,
        }


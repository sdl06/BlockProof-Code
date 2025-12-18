"""
Unit tests for verification_views.py
Tests public verification endpoints.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status
from credentials.models import Credential
from institutions.models import Institution
import time


class VerificationViewsTest(TestCase):
    """Test cases for verification endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear URL caches to avoid converter conflicts
        from django.urls import clear_url_caches
        clear_url_caches()
        
        self.client = APIClient()
        
        # Create test institution
        self.institution = Institution.objects.create(
            address="0x1234567890123456789012345678901234567890",
            name="Test University",
            created_at=int(time.time()),
            last_updated_at=int(time.time())
        )
        
        # Create test credential
        self.credential = Credential.objects.create(
            credential_id=1,
            student_wallet="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            institution=self.institution,
            fingerprint="0x" + "a" * 64,
            metadata_uri="ipfs://test123",
            encrypted_payload_uri="ipfs://test456",
            issued_at=int(time.time()),
            expires_at=None,
            revoked=False
        )
    
    def test_verify_from_link_valid(self):
        """Test verification with valid credential and matching fingerprint."""
        fingerprint = "0x" + "a" * 64
        
        response = self.client.get(f'/verify/1/{fingerprint}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'VALID')
        self.assertTrue(data['fingerprint_match'])
        self.assertTrue(data['valid'])
        self.assertEqual(data['credential_id'], 1)
        self.assertEqual(data['source'], 'cache')
    
    def test_verify_from_link_tampered(self):
        """Test verification with mismatched fingerprint (tampered)."""
        wrong_fingerprint = "0x" + "b" * 64
        
        response = self.client.get(f'/verify/1/{wrong_fingerprint}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'TAMPERED')
        self.assertFalse(data['fingerprint_match'])
    
    def test_verify_from_link_not_found(self):
        """Test verification with non-existent credential."""
        fingerprint = "0x" + "a" * 64
        
        response = self.client.get(f'/verify/999/{fingerprint}/')
        
        # Should fall back to blockchain or return NOT_FOUND
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
    
    def test_verify_from_link_invalid_credential_id(self):
        """Test verification with invalid credential ID format."""
        fingerprint = "0x" + "a" * 64
        
        # Django URL routing will return 404 for non-integer, not 400
        # The view itself handles the conversion, so this might be 404 or handled by view
        response = self.client.get(f'/verify/invalid/{fingerprint}/')
        
        # URL routing might return 404, or view might return 400
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])
    
    @patch('credentials.verification_views.get_blockproof_service')
    def test_verify_from_link_blockchain_fallback(self, mock_blockchain):
        """Test verification falling back to blockchain when not in cache."""
        mock_service = MagicMock()
        mock_service.verify_fingerprint.return_value = True
        mock_service.get_credential_status.return_value = {
            'valid': True,
            'revoked': False,
            'student_wallet': '0xtest',
            'institution': 'Test Uni',
            'issued_at': int(time.time()),
            'expires_at': None
        }
        mock_blockchain.return_value = mock_service
        
        fingerprint = "0x" + "c" * 64
        
        response = self.client.get(f'/verify/999/{fingerprint}/')
        
        # Should query blockchain
        mock_service.verify_fingerprint.assert_called_once()
    
    def test_verify_from_link_revoked_credential(self):
        """Test verification of revoked credential."""
        # Revoke the credential
        self.credential.revoked = True
        self.credential.revoked_at = int(time.time())
        self.credential.save()
        
        fingerprint = "0x" + "a" * 64
        response = self.client.get(f'/verify/1/{fingerprint}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'INVALID')
        self.assertTrue(data['revoked'])
    
    def test_verify_from_link_expired_credential(self):
        """Test verification of expired credential."""
        # Set expiration in the past
        self.credential.expires_at = int(time.time()) - 86400  # 1 day ago
        self.credential.save()
        
        fingerprint = "0x" + "a" * 64
        response = self.client.get(f'/verify/1/{fingerprint}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'INVALID')
        self.assertTrue(data['expired'])








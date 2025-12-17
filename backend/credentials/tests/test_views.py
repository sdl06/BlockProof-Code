"""
Unit tests for views.py
Tests credential issuance endpoint with file uploads.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from credentials.models import Credential
from institutions.models import Institution


class CredentialIssueViewTest(TestCase):
    """Test cases for credential issue endpoint."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear URL caches to avoid converter conflicts
        from django.urls import clear_url_caches
        clear_url_caches()
        
        self.client = APIClient()
        self.institution_address = "0x1234567890123456789012345678901234567890"
        self.student_wallet = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
    
    @patch('credentials.views.get_blockproof_service')
    @patch('credentials.views.get_ipfs_service')
    @patch('credentials.views.get_document_service')
    def test_issue_credential_with_file(self, mock_doc_service, mock_ipfs, mock_blockchain):
        """Test issuing credential with diploma file upload."""
        # Setup mocks
        mock_ipfs_instance = MagicMock()
        mock_ipfs_instance.upload_json.return_value = "ipfs://test123"
        mock_ipfs.return_value = mock_ipfs_instance
        
        mock_doc_instance = MagicMock()
        mock_doc_instance.generate_file_hash.return_value = "0x" + "a" * 64
        mock_doc_instance.generate_credential_fingerprint.return_value = "0x" + "b" * 64
        mock_doc_instance.check_holograph_ocr.return_value = {
            'ocr_extracted': True,
            'ocr_text': 'Test diploma',
            'service_used': 'ocr.space'
        }
        mock_doc_instance.save_diploma_file.return_value = "diplomas/test.pdf"
        mock_doc_service.return_value = mock_doc_instance
        
        mock_blockchain_instance = MagicMock()
        mock_blockchain_instance.issue_credential.return_value = "0xtx123"
        mock_blockchain.return_value = mock_blockchain_instance
        
        # Create test file
        test_file = SimpleUploadedFile(
            "diploma.pdf",
            b"test diploma content",
            content_type="application/pdf"
        )
        
        # Make request
        data = {
            'institution_address': self.institution_address,
            'student_wallet': self.student_wallet,
            'student_name': 'John Doe',
            'degree_type': 'Bachelor of Science',
            'graduation_year': 2024,
            'diploma_file': test_file,
        }
        
        response = self.client.post('/api/credentials/issue/', data, format='multipart')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        response_data = response.json()
        self.assertIn('transaction_hash', response_data)
        self.assertIn('fingerprint', response_data)
        self.assertIn('file_hash', response_data)
        self.assertIn('share_link_template', response_data)
        
        # Verify mocks were called
        mock_doc_instance.generate_file_hash.assert_called_once()
        mock_doc_instance.check_holograph_ocr.assert_called_once()
        mock_blockchain_instance.issue_credential.assert_called_once()
    
    @patch('credentials.views.get_blockproof_service')
    @patch('credentials.views.get_ipfs_service')
    def test_issue_credential_without_file(self, mock_ipfs, mock_blockchain):
        """Test issuing credential without file upload."""
        # Setup mocks
        mock_ipfs_instance = MagicMock()
        mock_ipfs_instance.upload_json.return_value = "ipfs://test123"
        mock_ipfs_instance.generate_fingerprint.return_value = "0x" + "c" * 64
        mock_ipfs.return_value = mock_ipfs_instance
        
        mock_blockchain_instance = MagicMock()
        mock_blockchain_instance.issue_credential.return_value = "0xtx456"
        mock_blockchain.return_value = mock_blockchain_instance
        
        # Make request
        data = {
            'institution_address': self.institution_address,
            'student_wallet': self.student_wallet,
            'student_name': 'Jane Doe',
            'degree_type': 'Master of Arts',
            'graduation_year': 2023,
        }
        
        response = self.client.post('/api/credentials/issue/', data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        response_data = response.json()
        self.assertIn('transaction_hash', response_data)
        self.assertIn('fingerprint', response_data)
    
    def test_issue_credential_validation_error(self):
        """Test credential issuance with invalid data."""
        data = {
            'institution_address': 'invalid',  # Too short
            'student_wallet': self.student_wallet,
        }
        
        response = self.client.post('/api/credentials/issue/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('institution_address', response.json())
    
    @patch('credentials.views.get_blockproof_service')
    @patch('credentials.views.get_ipfs_service')
    def test_issue_credential_blockchain_failure(self, mock_ipfs, mock_blockchain):
        """Test handling of blockchain transaction failure."""
        mock_ipfs_instance = MagicMock()
        mock_ipfs_instance.upload_json.return_value = "ipfs://test123"
        mock_ipfs_instance.generate_fingerprint.return_value = "0x" + "d" * 64
        mock_ipfs.return_value = mock_ipfs_instance
        
        mock_blockchain_instance = MagicMock()
        mock_blockchain_instance.issue_credential.return_value = None  # Failure
        mock_blockchain.return_value = mock_blockchain_instance
        
        data = {
            'institution_address': self.institution_address,
            'student_wallet': self.student_wallet,
        }
        
        response = self.client.post('/api/credentials/issue/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.json())
    
    @patch('credentials.views.get_blockproof_service')
    @patch('credentials.views.get_ipfs_service')
    def test_issue_credential_ipfs_failure(self, mock_ipfs, mock_blockchain):
        """Test handling of IPFS upload failure."""
        mock_ipfs_instance = MagicMock()
        mock_ipfs_instance.upload_json.return_value = None  # Failure
        mock_ipfs.return_value = mock_ipfs_instance
        
        data = {
            'institution_address': self.institution_address,
            'student_wallet': self.student_wallet,
        }
        
        response = self.client.post('/api/credentials/issue/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.json())





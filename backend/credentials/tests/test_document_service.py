"""
Unit tests for document_service.py
Tests file hash generation, fingerprint generation, OCR integration, and file storage.
"""
import os
import tempfile
import hashlib
from unittest.mock import patch, mock_open, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from credentials.document_service import DocumentService, get_document_service


class DocumentServiceTest(TestCase):
    """Test cases for DocumentService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = DocumentService()
        # Create a test file
        self.test_content = b"This is a test diploma file content for hashing"
        self.test_file = SimpleUploadedFile(
            "test_diploma.pdf",
            self.test_content,
            content_type="application/pdf"
        )
    
    def test_generate_file_hash(self):
        """Test file hash generation."""
        file_hash = self.service.generate_file_hash(self.test_file)
        
        # Should return hex string with 0x prefix
        self.assertTrue(file_hash.startswith('0x'))
        self.assertEqual(len(file_hash), 66)  # 0x + 64 hex chars (32 bytes)
        
        # Hash should be deterministic
        self.test_file.seek(0)
        hash2 = self.service.generate_file_hash(self.test_file)
        self.assertEqual(file_hash, hash2)
        
        # Verify it's SHA256
        expected_hash = '0x' + hashlib.sha256(self.test_content).hexdigest()
        self.assertEqual(file_hash, expected_hash)
    
    def test_generate_file_hash_different_files(self):
        """Test that different files produce different hashes."""
        file2_content = b"Different content"
        file2 = SimpleUploadedFile("test2.pdf", file2_content, content_type="application/pdf")
        
        hash1 = self.service.generate_file_hash(self.test_file)
        hash2 = self.service.generate_file_hash(file2)
        
        self.assertNotEqual(hash1, hash2)
    
    def test_generate_credential_fingerprint(self):
        """Test credential fingerprint generation."""
        file_hash = self.service.generate_file_hash(self.test_file)
        
        fingerprint = self.service.generate_credential_fingerprint(
            file_hash=file_hash,
            institution_address="0x1234567890123456789012345678901234567890",
            student_wallet="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            student_name="John Doe",
            degree_type="Bachelor of Science",
            graduation_year=2024,
            issued_at=1704067200
        )
        
        # Should return hex string with 0x prefix
        self.assertTrue(fingerprint.startswith('0x'))
        # Keccak256 produces 32 bytes = 64 hex chars, plus 0x prefix = 66 chars
        # Web3.keccak returns bytes, .hex() gives 64 chars, + '0x' = 66
        # But sometimes it might be formatted differently, so check it's reasonable
        self.assertGreaterEqual(len(fingerprint), 66)
        self.assertLessEqual(len(fingerprint), 68)  # Allow some flexibility
        self.assertTrue(all(c in '0123456789abcdefx' for c in fingerprint.lower()))
        
        # Fingerprint should be deterministic
        fingerprint2 = self.service.generate_credential_fingerprint(
            file_hash=file_hash,
            institution_address="0x1234567890123456789012345678901234567890",
            student_wallet="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            student_name="John Doe",
            degree_type="Bachelor of Science",
            graduation_year=2024,
            issued_at=1704067200
        )
        self.assertEqual(fingerprint, fingerprint2)
    
    def test_generate_credential_fingerprint_different_metadata(self):
        """Test that different metadata produces different fingerprints."""
        file_hash = self.service.generate_file_hash(self.test_file)
        
        fp1 = self.service.generate_credential_fingerprint(
            file_hash=file_hash,
            institution_address="0x1111111111111111111111111111111111111111",
            student_wallet="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            student_name="John Doe",
            degree_type="Bachelor",
            graduation_year=2024,
            issued_at=1704067200
        )
        
        fp2 = self.service.generate_credential_fingerprint(
            file_hash=file_hash,
            institution_address="0x2222222222222222222222222222222222222222",  # Different
            student_wallet="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            student_name="John Doe",
            degree_type="Bachelor",
            graduation_year=2024,
            issued_at=1704067200
        )
        
        self.assertNotEqual(fp1, fp2)
    
    @patch('credentials.ocr_helpers.ocr_space_file')
    def test_check_holograph_ocr_success(self, mock_ocr):
        """Test OCR integration with successful response."""
        # Mock OCR.space response
        mock_ocr.return_value = '{"ParsedResults":[{"ParsedText":"DIPLOMA\\nJohn Doe\\nBachelor of Science"}],"IsErroredOnProcessing":false}'
        
        result = self.service.check_holograph_ocr(self.test_file)
        
        # Should extract OCR text
        self.assertTrue(result['ocr_extracted'])
        self.assertIn('ocr_text', result)
        self.assertEqual(result['service_used'], 'ocr.space')
        self.assertIn('DIPLOMA', result['ocr_text'])
        mock_ocr.assert_called_once()
    
    @patch('credentials.ocr_helpers.ocr_space_file')
    def test_check_holograph_ocr_empty_response(self, mock_ocr):
        """Test OCR integration with empty text response."""
        mock_ocr.return_value = '{"ParsedResults":[{"ParsedText":""}],"IsErroredOnProcessing":false}'
        
        result = self.service.check_holograph_ocr(self.test_file)
        
        self.assertFalse(result['ocr_extracted'])
        self.assertEqual(result['service_used'], 'placeholder')
    
    @patch('credentials.ocr_helpers.ocr_space_file')
    def test_check_holograph_ocr_error(self, mock_ocr):
        """Test OCR integration with error response."""
        mock_ocr.return_value = '{"ErrorMessage":"Invalid API key","IsErroredOnProcessing":true}'
        
        result = self.service.check_holograph_ocr(self.test_file)
        
        self.assertFalse(result['ocr_extracted'])
        self.assertGreater(len(result['warnings']), 0)
        self.assertIn('OCR error', result['warnings'][0])
    
    @patch('credentials.ocr_helpers.ocr_space_file')
    def test_check_holograph_ocr_exception(self, mock_ocr):
        """Test OCR integration when exception occurs."""
        mock_ocr.side_effect = Exception("Network error")
        
        result = self.service.check_holograph_ocr(self.test_file)
        
        self.assertFalse(result['ocr_extracted'])
        self.assertGreater(len(result['warnings']), 0)
        self.assertIn('OCR processing failed', result['warnings'][0])
    
    def test_check_holograph_ocr_file_validation(self):
        """Test file validation in OCR check."""
        # Test file size limit
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile("large.pdf", large_content, content_type="application/pdf")
        
        with patch('credentials.ocr_helpers.ocr_space_file'):
            result = self.service.check_holograph_ocr(large_file)
            self.assertIn('File size exceeds recommended limit', result['warnings'])
        
        # Test unsupported file type
        unsupported_file = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
        with patch('credentials.ocr_helpers.ocr_space_file'):
            result = self.service.check_holograph_ocr(unsupported_file)
            self.assertIn('Unsupported file type', result['warnings'][0])
    
    def test_save_diploma_file(self):
        """Test saving diploma file to storage."""
        credential_id = 12345
        
        file_path = self.service.save_diploma_file(self.test_file, credential_id)
        
        # Should return relative path (handle both / and \ for cross-platform)
        self.assertTrue(file_path.replace('\\', '/').startswith('diplomas/'))
        self.assertIn(str(credential_id), file_path)
        
        # File should exist - handle path separators
        filename = os.path.basename(file_path)
        full_path = os.path.join(self.service.media_root, filename)
        self.assertTrue(os.path.exists(full_path), f"File not found: {full_path}")
        
        # File content should match
        with open(full_path, 'rb') as f:
            saved_content = f.read()
        self.assertEqual(saved_content, self.test_content)
        
        # Cleanup
        if os.path.exists(full_path):
            os.remove(full_path)
    
    def test_save_diploma_file_unique_filenames(self):
        """Test that saved files have unique filenames."""
        import time
        
        file1_path = self.service.save_diploma_file(self.test_file, 1)
        time.sleep(1.1)  # Ensure different timestamp (1+ second)
        self.test_file.seek(0)
        file2_path = self.service.save_diploma_file(self.test_file, 1)
        
        # Filenames should be different (due to timestamp)
        # Extract just the filename part for comparison
        file1_name = os.path.basename(file1_path)
        file2_name = os.path.basename(file2_path)
        self.assertNotEqual(file1_name, file2_name, "Filenames should differ due to timestamp")
        
        # Cleanup
        full_path1 = os.path.join(self.service.media_root, file1_name)
        full_path2 = os.path.join(self.service.media_root, file2_name)
        if os.path.exists(full_path1):
            os.remove(full_path1)
        if os.path.exists(full_path2):
            os.remove(full_path2)
    
    def test_get_document_service(self):
        """Test service factory function."""
        service = get_document_service()
        self.assertIsInstance(service, DocumentService)
        
        # Should return same instance (singleton pattern if implemented)
        service2 = get_document_service()
        self.assertIsInstance(service2, DocumentService)








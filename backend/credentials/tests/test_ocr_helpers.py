"""
Unit tests for ocr_helpers.py
Tests OCR.space API integration functions.
"""
import os
import json
import tempfile
from unittest.mock import patch, mock_open, MagicMock
from django.test import TestCase
from credentials.ocr_helpers import ocr_space_file, ocr_space_url


class OCRHelpersTest(TestCase):
    """Test cases for OCR helper functions."""
    
    @patch('credentials.ocr_helpers.requests.post')
    def test_ocr_space_file_success(self, mock_post):
        """Test successful OCR.space file upload."""
        # Mock response
        mock_response = MagicMock()
        mock_response.content.decode.return_value = json.dumps({
            "ParsedResults": [{
                "ParsedText": "Test diploma text",
                "TextOverlay": {}
            }],
            "IsErroredOnProcessing": False
        })
        mock_post.return_value = mock_response
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            tmp.write(b"fake image content")
            tmp_path = tmp.name
        
        try:
            result = ocr_space_file(tmp_path, overlay=False, api_key='test_key', language='eng')
            
            # Should return JSON string
            self.assertIsInstance(result, str)
            parsed = json.loads(result)
            self.assertIn('ParsedResults', parsed)
            
            # Verify API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertEqual(call_args[0][0], 'https://api.ocr.space/parse/image')
            
            # Verify payload
            self.assertIn('apikey', call_args[1]['data'])
            self.assertEqual(call_args[1]['data']['apikey'], 'test_key')
            self.assertEqual(call_args[1]['data']['language'], 'eng')
            self.assertFalse(call_args[1]['data']['isOverlayRequired'])
            
            # Verify file was included
            self.assertIn('files', call_args[1])
        finally:
            os.unlink(tmp_path)
    
    @patch('credentials.ocr_helpers.requests.post')
    def test_ocr_space_file_defaults(self, mock_post):
        """Test OCR.space file upload with default parameters."""
        mock_response = MagicMock()
        mock_response.content.decode.return_value = '{"ParsedResults":[]}'
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            tmp.write(b"content")
            tmp_path = tmp.name
        
        try:
            result = ocr_space_file(tmp_path)
            
            # Should use default API key
            call_args = mock_post.call_args
            self.assertEqual(call_args[1]['data']['apikey'], 'helloworld')
            self.assertEqual(call_args[1]['data']['language'], 'eng')
            self.assertFalse(call_args[1]['data']['isOverlayRequired'])
        finally:
            os.unlink(tmp_path)
    
    @patch('credentials.ocr_helpers.requests.post')
    def test_ocr_space_file_overlay(self, mock_post):
        """Test OCR.space file upload with overlay enabled."""
        mock_response = MagicMock()
        mock_response.content.decode.return_value = '{"ParsedResults":[]}'
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            tmp.write(b"content")
            tmp_path = tmp.name
        
        try:
            ocr_space_file(tmp_path, overlay=True)
            
            call_args = mock_post.call_args
            self.assertTrue(call_args[1]['data']['isOverlayRequired'])
        finally:
            os.unlink(tmp_path)
    
    @patch('credentials.ocr_helpers.requests.post')
    def test_ocr_space_url_success(self, mock_post):
        """Test successful OCR.space URL request."""
        mock_response = MagicMock()
        mock_response.content.decode.return_value = json.dumps({
            "ParsedResults": [{"ParsedText": "Extracted text"}],
            "IsErroredOnProcessing": False
        })
        mock_post.return_value = mock_response
        
        result = ocr_space_url('http://example.com/image.png')
        
        # Should return JSON string
        parsed = json.loads(result)
        self.assertIn('ParsedResults', parsed)
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], 'https://api.ocr.space/parse/image')
        self.assertEqual(call_args[1]['data']['url'], 'http://example.com/image.png')
    
    @patch('credentials.ocr_helpers.requests.post')
    def test_ocr_space_url_defaults(self, mock_post):
        """Test OCR.space URL request with default parameters."""
        mock_response = MagicMock()
        mock_response.content.decode.return_value = '{"ParsedResults":[]}'
        mock_post.return_value = mock_response
        
        ocr_space_url('http://example.com/image.png')
        
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['data']['apikey'], 'helloworld')
        self.assertEqual(call_args[1]['data']['language'], 'eng')
    
    @patch('credentials.ocr_helpers.requests.post')
    def test_ocr_space_file_error_handling(self, mock_post):
        """Test error handling in OCR.space file upload."""
        mock_post.side_effect = Exception("Network error")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            tmp.write(b"content")
            tmp_path = tmp.name
        
        try:
            with self.assertRaises(Exception):
                ocr_space_file(tmp_path)
        finally:
            os.unlink(tmp_path)









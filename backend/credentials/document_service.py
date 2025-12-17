"""
Document processing service for diploma verification.
Handles file uploads, hash generation, and holograph OCR detection.
"""
import hashlib
import logging
import os
from typing import Optional, Tuple, Dict, Any
from django.core.files.uploadedfile import UploadedFile
from web3 import Web3
import json

logger = logging.getLogger('credentials')


class DocumentService:
    """Service for processing diploma documents."""
    
    def __init__(self):
        self.media_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media', 'diplomas')
        os.makedirs(self.media_root, exist_ok=True)
    
    def generate_file_hash(self, file: UploadedFile) -> str:
        """
        Generate SHA256 hash of uploaded file.
        This hash is used for tamper detection.
        """
        file.seek(0)  # Reset file pointer
        hash_obj = hashlib.sha256()
        
        # Read file in chunks to handle large files
        for chunk in file.chunks():
            hash_obj.update(chunk)
        
        file.seek(0)  # Reset for potential reuse
        return '0x' + hash_obj.hexdigest()
    
    def generate_credential_fingerprint(
        self,
        file_hash: str,
        institution_address: str,
        student_wallet: str,
        student_name: str,
        passport_number: str,
        degree_type: str,
        graduation_year: int,
        issued_at: int
    ) -> str:
        """
        Generate cryptographic fingerprint from diploma file and metadata.
        This is the hash that gets stored on the blockchain.
        """
        # Create canonical representation
        fingerprint_data = {
            'file_hash': file_hash,
            'institution_address': institution_address,
            'student_wallet': student_wallet,
            'student_name': student_name,
            'passport_number': passport_number,
            'degree_type': degree_type,
            'graduation_year': graduation_year,
            'issued_at': issued_at,
        }
        
        # Convert to sorted JSON string for consistency
        json_str = json.dumps(fingerprint_data, sort_keys=True, separators=(',', ':'))
        
        # Generate keccak256 hash (32 bytes)
        fingerprint_bytes = Web3.keccak(text=json_str)

        # web3 HexBytes.hex() may already include "0x" depending on version.
        fp_hex = fingerprint_bytes.hex()
        return fp_hex if fp_hex.startswith('0x') else ('0x' + fp_hex)
    
    def check_holograph_ocr(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Check for holograph/security features in the document.
        This helps detect fraud by verifying document authenticity.
        
        Options for integration:
        1. OCR.space API (FREE: 25K requests/month) - https://ocr.space/ocrapi
        2. Tesseract OCR (FREE, open source) - requires pytesseract
        3. Arya.ai Hologram Detection (paid, specialized)
        4. Custom OpenCV-based detection (free, requires development)
        
        See HOLOGRAPH_OCR_OPTIONS.md for detailed options.
        """
        file.seek(0)
        file_size = file.size
        
        # Basic checks
        checks = {
            'file_size': file_size,
            'file_type': file.content_type,
            'has_holograph_features': False,  # Placeholder - integrate service
            'ocr_extracted': False,  # Placeholder - integrate OCR service
            'authenticity_score': 0.0,  # Placeholder
            'warnings': [],
            'service_used': 'placeholder',
        }
        
        # Basic validation
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            checks['warnings'].append('File size exceeds recommended limit')
        
        if file.content_type not in ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']:
            checks['warnings'].append(f'Unsupported file type: {file.content_type}')
        
        # OCR.space API integration (free tier: 25K/month)
        # Using helper function that matches OCR.space documentation exactly
        try:
            import tempfile
            from .ocr_helpers import ocr_space_file
            
            # Save file temporarily for OCR
            file_ext = os.path.splitext(file.name)[1] or '.png'
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                for chunk in file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            
            # Get API key and language from environment
            ocr_space_key = os.getenv('OCR_SPACE_API_KEY', 'helloworld')  # 'helloworld' is free demo key
            language = os.getenv('OCR_LANGUAGE', 'eng')  # Default to English
            
            # Call OCR.space using the documented helper function
            result_json = ocr_space_file(
                filename=tmp_path,
                overlay=False,
                api_key=ocr_space_key,
                language=language
            )
            
            # Parse JSON response
            import json
            ocr_result = json.loads(result_json)
            
            if ocr_result.get('ParsedResults') and len(ocr_result['ParsedResults']) > 0:
                parsed_result = ocr_result['ParsedResults'][0]
                parsed_text = parsed_result.get('ParsedText', '').strip()
                
                if parsed_text:
                    checks['ocr_extracted'] = True
                    checks['ocr_text'] = parsed_text
                    checks['ocr_confidence'] = True  # OCR.space doesn't provide confidence in free tier
                    checks['service_used'] = 'ocr.space'
                    logger.info(f"OCR.space extracted {len(parsed_text)} chars from {file.name}")
                else:
                    logger.warning(f"OCR.space returned empty text for {file.name}")
            elif ocr_result.get('ErrorMessage'):
                error_msg = ocr_result.get('ErrorMessage')
                checks['warnings'].append(f"OCR error: {error_msg}")
                logger.warning(f"OCR.space error: {error_msg}")
            
            # Clean up temporary file
            os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f"OCR.space integration failed: {e}", exc_info=True)
            checks['warnings'].append(f"OCR processing failed: {str(e)}")
        
        # TODO: Integrate hologram detection
        # Options:
        # 1. Arya.ai Hologram Detection API (paid)
        # 2. Custom OpenCV-based detection (see HOLOGRAPH_OCR_OPTIONS.md)
        # 3. Veryfi Fraud Detection (paid, min $500/month)
        
        logger.info(f"Holograph OCR check for file: {file.name} (service: {checks['service_used']})")
        
        return checks
    
    def save_diploma_file(self, file: UploadedFile, credential_id: int) -> str:
        """
        Save uploaded diploma file to blob storage (file system for now).
        Returns the file path relative to MEDIA_ROOT.
        
        For a toy app, we're using file storage. In production, this would
        be replaced with proper blob storage (S3, Azure Blob, etc.).
        """
        # Generate safe filename
        ext = os.path.splitext(file.name)[1] or '.pdf'
        # Use credential_id and timestamp for uniqueness
        import time
        timestamp = int(time.time())
        safe_name = hashlib.md5(file.name.encode()).hexdigest()[:8]
        filename = f'credential_{credential_id}_{timestamp}_{safe_name}{ext}'
        filepath = os.path.join(self.media_root, filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save file (blob storage - file system for now)
        file.seek(0)  # Reset file pointer
        with open(filepath, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        file.seek(0)  # Reset for potential reuse
        
        logger.info(f"Saved diploma file: {filename} ({os.path.getsize(filepath)} bytes)")
        
        # Return relative path
        return os.path.join('diplomas', filename)


def get_document_service() -> DocumentService:
    """Get the document service instance."""
    return DocumentService()





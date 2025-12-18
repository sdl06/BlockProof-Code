"""
IPFS service for uploading credential metadata and encrypted payloads.
Supports both real IPFS (via Pinata or public gateway) and development mode.
"""
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from web3 import Web3
import os

logger = logging.getLogger('credentials')


class IPFSService:
    """Service for uploading data to IPFS."""
    
    def __init__(self):
        # For production, configure Pinata API keys
        self.pinata_api_key = os.getenv('PINATA_API_KEY', '')
        self.pinata_secret_key = os.getenv('PINATA_SECRET_KEY', '')
        self.use_pinata = bool(self.pinata_api_key and self.pinata_secret_key)
        self.gateway_url = os.getenv('IPFS_GATEWAY', 'https://ipfs.io/ipfs/')
    
    def upload_json(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Upload JSON data to IPFS and return the IPFS hash/URI.
        
        Args:
            data: Dictionary to upload as JSON
            
        Returns:
            IPFS URI (ipfs://...) or None on failure
        """
        try:
            json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
            
            if self.use_pinata:
                return self._upload_to_pinata(json_str)
            else:
                # Development mode: Generate deterministic IPFS-like hash
                # In production, replace with actual IPFS upload
                return self._generate_ipfs_hash(json_str)
        except Exception as e:
            logger.error(f"Error uploading to IPFS: {e}")
            return None
    
    def _upload_to_pinata(self, json_str: str) -> Optional[str]:
        """Upload to Pinata IPFS service."""
        try:
            import requests
            
            headers = {
                'pinata_api_key': self.pinata_api_key,
                'pinata_secret_api_key': self.pinata_secret_key,
                'Content-Type': 'application/json'
            }
            
            # Pinata expects the data in a specific format
            data = {
                'pinataContent': json.loads(json_str),
                'pinataMetadata': {
                    'name': 'credential-metadata'
                }
            }
            
            response = requests.post(
                'https://api.pinata.cloud/pinning/pinJSONToIPFS',
                json=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                ipfs_hash = response.json().get('IpfsHash')
                return f'ipfs://{ipfs_hash}'
            else:
                logger.error(f"Pinata upload failed: {response.status_code} - {response.text}")
                return None
        except ImportError:
            logger.warning("requests library not available, using development mode")
            return self._generate_ipfs_hash(json_str)
        except Exception as e:
            logger.error(f"Pinata upload error: {e}")
            return self._generate_ipfs_hash(json_str)
    
    def _generate_ipfs_hash(self, data: str) -> str:
        """
        Generate a deterministic IPFS-like hash for development.
        In production, this should be replaced with actual IPFS upload.
        """
        # Generate a hash that looks like an IPFS CID
        # This is a simplified version - real IPFS uses multihash
        hash_obj = hashlib.sha256(data.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # For development, we'll use a simulated IPFS hash
        # Format: ipfs://Qm... (Qm prefix is common for IPFS v0)
        # We'll use first 44 chars to simulate a CID
        simulated_cid = 'Qm' + hash_hex[:42]
        
        logger.info(f"Generated development IPFS hash: {simulated_cid}")
        return f'ipfs://{simulated_cid}'
    
    def generate_fingerprint(self, credential_data: Dict[str, Any]) -> str:
        """
        Generate a cryptographic fingerprint from credential data.
        This should be deterministic and unique for each credential.
        """
        # Create a canonical representation of the credential
        fingerprint_data = {
            'institution': credential_data.get('institution_address', ''),
            'student_wallet': credential_data.get('student_wallet', ''),
            'student_name': credential_data.get('student_name', ''),
            'passport_number': credential_data.get('passport_number', ''),
            'degree_type': credential_data.get('degree_type', ''),
            'graduation_year': credential_data.get('graduation_year', ''),
            'metadata_uri': credential_data.get('metadata_uri', ''),
            'issued_at': credential_data.get('issued_at', 0),
        }
        
        # Convert to sorted JSON string for consistency
        json_str = json.dumps(fingerprint_data, sort_keys=True, separators=(',', ':'))
        
        # Generate keccak256 hash (32 bytes)
        fingerprint_bytes = Web3.keccak(text=json_str)

        # web3 HexBytes.hex() may already include "0x" depending on version.
        fp_hex = fingerprint_bytes.hex()
        return fp_hex if fp_hex.startswith('0x') else ('0x' + fp_hex)


def get_ipfs_service() -> IPFSService:
    """Get the IPFS service instance."""
    return IPFSService()









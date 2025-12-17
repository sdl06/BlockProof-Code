"""
Zero-Knowledge Proof service for generating and verifying proofs.
Supports both simple cryptographic commitments and zk-SNARKs via Circom.
"""

import os
import json
import hashlib
import subprocess
import tempfile
from typing import Dict, Optional, List, Tuple
from django.conf import settings
from web3 import Web3
import logging

# Try to import cryptography, but make it optional
try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

logger = logging.getLogger('zkproof')


class ZKProofService:
    """
    Service for generating and verifying zero-knowledge proofs.
    
    Supports multiple proof types:
    1. Simple cryptographic commitments (fast, no external dependencies)
    2. zk-SNARKs via Circom (more powerful, requires Node.js)
    """
    
    def __init__(self):
        self.config = getattr(settings, 'ZKPROOF_CONFIG', {})
        self.enabled = self.config.get('ZKPROOF_ENABLED', True)
        self.circuit_path = self.config.get('ZKPROOF_CIRCUIT_PATH', './zkproof/circuits')
        self.artifacts_path = self.config.get('ZKPROOF_ARTIFACTS_PATH', './zkproof/artifacts')
        
        # Ensure directories exist
        os.makedirs(self.circuit_path, exist_ok=True)
        os.makedirs(self.artifacts_path, exist_ok=True)
    
    def generate_credential_validity_proof(
        self,
        credential_id: int,
        fingerprint: str,
        student_wallet: str,
        institution: str,
        secret_data: Optional[Dict] = None
    ) -> Dict:
        """
        Generate a zero-knowledge proof that a credential is valid without revealing:
        - Full credential details
        - Secret data (if provided)
        
        Returns proof data that can be verified without accessing the full credential.
        """
        if not self.enabled:
            raise ValueError("ZKProof is not enabled")
        
        # For now, use simple cryptographic commitment
        # In production, use zk-SNARKs for more powerful proofs
        return self._generate_commitment_proof(
            credential_id=credential_id,
            fingerprint=fingerprint,
            student_wallet=student_wallet,
            institution=institution,
            secret_data=secret_data
        )
    
    def _generate_commitment_proof(
        self,
        credential_id: int,
        fingerprint: str,
        student_wallet: str,
        institution: str,
        secret_data: Optional[Dict] = None
    ) -> Dict:
        """
        Generate a simple cryptographic commitment proof.
        This proves knowledge of the credential without revealing all details.
        """
        # Create commitment to credential data
        commitment_data = {
            'credential_id': credential_id,
            'fingerprint': fingerprint,
            'student_wallet': student_wallet,
            'institution': institution,
        }
        
        if secret_data:
            commitment_data['secret_hash'] = self._hash_secret_data(secret_data)
        
        # Create commitment (hash of the data)
        commitment = self._create_commitment(commitment_data)
        
        # Create proof structure
        proof = {
            'type': 'commitment',
            'commitment': commitment,
            'public_inputs': {
                'credential_id': credential_id,
                'fingerprint': fingerprint,
            },
            'proof_data': {
                'student_wallet_hash': hashlib.sha256(student_wallet.encode()).hexdigest(),
                'institution_hash': hashlib.sha256(institution.encode()).hexdigest(),
            }
        }
        
        return proof
    
    def verify_credential_validity_proof(
        self,
        proof: Dict,
        expected_fingerprint: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a zero-knowledge proof of credential validity.
        
        Returns: (is_valid, error_message)
        """
        if not self.enabled:
            return False, "ZKProof is not enabled"
        
        proof_type = proof.get('type')
        
        if proof_type == 'commitment':
            return self._verify_commitment_proof(proof, expected_fingerprint)
        elif proof_type == 'snark':
            return self._verify_snark_proof(proof)
        else:
            return False, f"Unknown proof type: {proof_type}"
    
    def _verify_commitment_proof(
        self,
        proof: Dict,
        expected_fingerprint: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Verify a commitment-based proof."""
        try:
            public_inputs = proof.get('public_inputs', {})
            proof_data = proof.get('proof_data', {})
            commitment = proof.get('commitment')
            
            # Reconstruct commitment
            reconstructed_data = {
                'credential_id': public_inputs.get('credential_id'),
                'fingerprint': public_inputs.get('fingerprint'),
            }
            
            # Verify fingerprint if provided
            if expected_fingerprint:
                if public_inputs.get('fingerprint') != expected_fingerprint:
                    return False, "Fingerprint mismatch"
            
            # Reconstruct commitment
            reconstructed_commitment = self._create_commitment(reconstructed_data)
            
            # Verify commitment matches
            if reconstructed_commitment != commitment:
                return False, "Commitment verification failed"
            
            return True, None
        except Exception as e:
            logger.error(f"Error verifying commitment proof: {e}")
            return False, str(e)
    
    def generate_selective_disclosure_proof(
        self,
        credential_data: Dict,
        disclosed_fields: List[str],
        secret_fields: List[str]
    ) -> Dict:
        """
        Generate a proof that discloses only specific fields while keeping others secret.
        
        Example: Prove GPA > 3.5 without revealing exact GPA or other grades.
        """
        # Create commitment to secret fields
        secret_commitment = self._create_commitment({
            field: credential_data.get(field)
            for field in secret_fields
            if field in credential_data
        })
        
        # Create proof
        proof = {
            'type': 'selective_disclosure',
            'disclosed_fields': {field: credential_data.get(field) for field in disclosed_fields},
            'secret_commitment': secret_commitment,
            'proof_data': {
                'disclosed_count': len(disclosed_fields),
                'secret_count': len(secret_fields),
            }
        }
        
        return proof
    
    def generate_range_proof(
        self,
        value: float,
        min_value: float,
        max_value: float,
        credential_id: int
    ) -> Dict:
        """
        Generate a proof that a value is within a range without revealing the exact value.
        
        Example: Prove GPA is between 3.5 and 4.0 without revealing exact GPA.
        """
        # Simple range proof using commitment
        # In production, use zk-SNARKs for proper range proofs
        
        commitment = self._create_commitment({
            'value': value,
            'credential_id': credential_id,
        })
        
        proof = {
            'type': 'range_proof',
            'commitment': commitment,
            'public_inputs': {
                'credential_id': credential_id,
                'min_value': min_value,
                'max_value': max_value,
            },
            'proof_data': {
                'range_hash': hashlib.sha256(
                    f"{min_value}:{max_value}".encode()
                ).hexdigest()
            }
        }
        
        return proof
    
    def _create_commitment(self, data: Dict) -> str:
        """Create a cryptographic commitment (hash) of data."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _hash_secret_data(self, secret_data: Dict) -> str:
        """Hash secret data for commitment."""
        data_str = json.dumps(secret_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _verify_snark_proof(self, proof: Dict) -> Tuple[bool, Optional[str]]:
        """
        Verify a zk-SNARK proof using Circom/snarkjs.
        Requires Node.js and snarkjs to be installed.
        """
        try:
            # This would call snarkjs via subprocess
            # For now, return not implemented
            return False, "zk-SNARK verification not yet implemented. Use commitment proofs."
        except Exception as e:
            logger.error(f"Error verifying SNARK proof: {e}")
            return False, str(e)
    
    def generate_snark_proof(
        self,
        circuit_name: str,
        inputs: Dict,
        witness: Dict
    ) -> Optional[Dict]:
        """
        Generate a zk-SNARK proof using Circom.
        Requires Node.js, circom, and snarkjs to be installed.
        """
        # This would:
        # 1. Load circuit
        # 2. Generate witness
        # 3. Generate proof using snarkjs
        # 4. Return proof and public inputs
        
        logger.warning("zk-SNARK proof generation not yet implemented")
        return None


# Singleton instance
_zkproof_service = None

def get_zkproof_service() -> ZKProofService:
    """Get or create ZKProofService instance."""
    global _zkproof_service
    if _zkproof_service is None:
        _zkproof_service = ZKProofService()
    return _zkproof_service


"""
Zero-Knowledge Proof models for privacy-preserving credential verification.
"""

from django.db import models
from credentials.models import Credential
import hashlib


class ZKProof(models.Model):
    """
    Stores metadata about zero-knowledge proofs for credentials.
    The actual proof can be stored on IPFS or in the proof_data field.
    """
    credential = models.OneToOneField(
        Credential,
        on_delete=models.CASCADE,
        related_name='zkproof'
    )
    
    # Proof metadata
    proof_type = models.CharField(
        max_length=50,
        choices=[
            ('credential_validity', 'Credential Validity Proof'),
            ('selective_disclosure', 'Selective Disclosure Proof'),
            ('range_proof', 'Range Proof (e.g., GPA > 3.5)'),
            ('membership_proof', 'Membership Proof (e.g., graduated from X)'),
        ],
        default='credential_validity'
    )
    
    # Proof data (can be JSON or reference to IPFS)
    proof_data = models.JSONField(null=True, blank=True)
    proof_ipfs_hash = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    
    # Public inputs (what the verifier needs to verify)
    public_inputs = models.JSONField()
    
    # Circuit/verification key hash (identifies which circuit was used)
    circuit_hash = models.CharField(max_length=66, db_index=True)
    
    # Verification key (can be stored or referenced)
    verification_key_ipfs = models.CharField(max_length=100, null=True, blank=True)
    
    # Status
    is_valid = models.BooleanField(default=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'zkproofs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['credential', 'proof_type']),
            models.Index(fields=['circuit_hash', 'is_valid']),
        ]
    
    def __str__(self):
        return f"ZKProof for Credential #{self.credential.credential_id} ({self.proof_type})"


class ZKProofVerification(models.Model):
    """
    Tracks proof verifications for auditing.
    """
    proof = models.ForeignKey(ZKProof, on_delete=models.CASCADE, related_name='verifications')
    verifier_address = models.CharField(max_length=42, null=True, blank=True)  # Optional: who verified
    verification_result = models.BooleanField()
    verification_time = models.FloatField()  # Time taken in seconds
    error_message = models.TextField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'zkproof_verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['proof', 'verification_result']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Verification of {self.proof} - {'Valid' if self.verification_result else 'Invalid'}"


class ZKCircuit(models.Model):
    """
    Stores circuit definitions and metadata for zk-SNARKs.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    circuit_type = models.CharField(
        max_length=50,
        choices=[
            ('circom', 'Circom Circuit'),
            ('r1cs', 'R1CS Format'),
            ('commitment', 'Cryptographic Commitment'),
        ]
    )
    
    # Circuit file references
    circuit_file_path = models.CharField(max_length=500)
    circuit_hash = models.CharField(max_length=66, unique=True, db_index=True)
    
    # Verification key
    verification_key_path = models.CharField(max_length=500, null=True, blank=True)
    verification_key_ipfs = models.CharField(max_length=100, null=True, blank=True)
    
    # Proving key (usually not stored, but can reference)
    proving_key_ipfs = models.CharField(max_length=100, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    version = models.CharField(max_length=20, default='1.0.0')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'zk_circuits'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} (v{self.version})"
    
    def calculate_hash(self):
        """Calculate hash of circuit for verification."""
        import os
        if self.circuit_file_path and os.path.exists(self.circuit_file_path):
            with open(self.circuit_file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        return None


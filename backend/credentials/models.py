"""
Credential models that cache blockchain data.
This is the primary cost optimization: all reads come from database.
"""

from django.db import models
from institutions.models import Institution
import time


class Credential(models.Model):
    """
    Cached credential data from blockchain.
    Synced via event indexer to minimize RPC calls.
    """
    credential_id = models.BigIntegerField(unique=True, db_index=True)
    student_wallet = models.CharField(max_length=42, db_index=True)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='credentials')
    fingerprint = models.CharField(max_length=66, db_index=True)
    metadata_uri = models.URLField(max_length=500)
    encrypted_payload_uri = models.URLField(max_length=500)
    issued_at = models.BigIntegerField()
    expires_at = models.BigIntegerField(null=True, blank=True)
    revoked = models.BooleanField(default=False)
    revoked_at = models.BigIntegerField(null=True, blank=True)
    revocation_reason_hash = models.CharField(max_length=66, null=True, blank=True)

    # Extended metadata (toy-app friendly; source of truth remains IPFS + chain)
    student_name = models.CharField(max_length=200, blank=True, default="")
    passport_number = models.CharField(max_length=50, blank=True, default="", db_index=True)
    degree_type = models.CharField(max_length=100, blank=True, default="")
    graduation_year = models.IntegerField(null=True, blank=True)
    diploma_file_hash = models.CharField(max_length=66, null=True, blank=True)
    diploma_file_path = models.CharField(max_length=500, null=True, blank=True)
    transaction_hash = models.CharField(max_length=66, null=True, blank=True, db_index=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'credentials'
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['student_wallet', '-issued_at']),
            models.Index(fields=['fingerprint']),
        ]
    
    def is_valid(self) -> bool:
        """Check if credential is currently valid."""
        if self.revoked:
            return False
        if self.expires_at and self.expires_at < int(time.time()):
            return False
        return True
    
    def __str__(self):
        return f"Credential #{self.credential_id} - {self.student_wallet}"


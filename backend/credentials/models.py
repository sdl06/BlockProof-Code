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


class StudentVerificationRequest(models.Model):
    """
    Student-initiated verification request.
    After hologram OCR verification passes, this becomes a credential.
    """
    STATUS_PENDING = 'pending'
    STATUS_VERIFYING = 'verifying'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_VERIFYING, 'Verifying'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    
    # Student information
    student_name = models.CharField(max_length=200)
    passport_number = models.CharField(max_length=50, db_index=True)
    student_wallet = models.CharField(max_length=42, db_index=True)
    degree_type = models.CharField(max_length=100)
    graduation_date = models.DateField()
    
    # Institution (optional - can be auto-assigned or student selects)
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, related_name='verification_requests')
    
    # Document
    diploma_file = models.FileField(upload_to='verification_requests/')
    diploma_file_hash = models.CharField(max_length=66, db_index=True)
    
    # Verification results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    hologram_ocr_result = models.JSONField(null=True, blank=True)  # Store OCR/hologram check results
    hologram_verified = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True)
    
    # Result (if approved)
    credential = models.OneToOneField(Credential, on_delete=models.SET_NULL, null=True, blank=True, related_name='verification_request')
    share_link = models.URLField(max_length=500, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'student_verification_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['passport_number', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Verification Request #{self.id} - {self.student_name} ({self.status})"

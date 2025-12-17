"""
Blockchain event models for caching on-chain data.
This minimizes expensive RPC calls by maintaining a local cache.
"""

from django.db import models
from django.utils import timezone


class BlockchainEvent(models.Model):
    """Base model for tracking blockchain events."""
    block_number = models.BigIntegerField(db_index=True)
    transaction_hash = models.CharField(max_length=66, unique=True, db_index=True)
    log_index = models.IntegerField()
    processed = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        ordering = ['-block_number', '-log_index']


class CredentialIssuedEvent(BlockchainEvent):
    """Cached CredentialIssued events from the contract."""
    credential_id = models.BigIntegerField(unique=True, db_index=True)
    student_wallet = models.CharField(max_length=42, db_index=True)
    institution = models.CharField(max_length=42, db_index=True)
    fingerprint = models.CharField(max_length=66, db_index=True)
    metadata_uri = models.URLField(max_length=500)
    encrypted_payload_uri = models.URLField(max_length=500)
    expires_at = models.BigIntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'blockchain_credential_issued'


class CredentialRevokedEvent(BlockchainEvent):
    """Cached CredentialRevoked events from the contract."""
    credential_id = models.BigIntegerField(db_index=True)
    revoked_by = models.CharField(max_length=42)
    reason_hash = models.CharField(max_length=66)
    revoked_at = models.BigIntegerField()
    
    class Meta:
        db_table = 'blockchain_credential_revoked'


class IndexerState(models.Model):
    """Tracks the last processed block to enable incremental indexing."""
    key = models.CharField(max_length=100, unique=True)
    last_processed_block = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'blockchain_indexer_state'
    
    @classmethod
    def get_last_block(cls, key='default'):
        obj, _ = cls.objects.get_or_create(key=key, defaults={'last_processed_block': 0})
        return obj.last_processed_block
    
    @classmethod
    def update_last_block(cls, key='default', block_number=None):
        obj, _ = cls.objects.get_or_create(key=key)
        if block_number is not None:
            obj.last_processed_block = block_number
            obj.save()


"""
Institution models that cache blockchain data.
"""

from django.db import models


class Institution(models.Model):
    """
    Cached institution data from blockchain.
    """
    address = models.CharField(max_length=42, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.BigIntegerField()
    last_updated_at = models.BigIntegerField()
    
    # Metadata
    cached_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'institutions'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.address})"


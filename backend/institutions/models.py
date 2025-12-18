"""
Institution models that cache blockchain data.
"""

from django.db import models
from django.contrib.auth.models import User
import secrets


class Institution(models.Model):
    """
    Cached institution data from blockchain.
    """
    address = models.CharField(max_length=42, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.BigIntegerField()
    last_updated_at = models.BigIntegerField()
    
    # Authentication - link to Django User for login/password
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='institution_profile')
    api_key = models.CharField(max_length=64, unique=True, db_index=True, null=True, blank=True)
    
    # Metadata
    cached_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'institutions'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.address})"
    
    def generate_api_key(self):
        """Generate a secure API key for this institution."""
        if not self.api_key:
            self.api_key = secrets.token_urlsafe(32)
            self.save(update_fields=['api_key'])
        return self.api_key


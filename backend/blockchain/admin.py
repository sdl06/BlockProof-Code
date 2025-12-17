from django.contrib import admin
from .models import (
    CredentialIssuedEvent,
    CredentialRevokedEvent,
    IndexerState
)


@admin.register(CredentialIssuedEvent)
class CredentialIssuedEventAdmin(admin.ModelAdmin):
    list_display = ['credential_id', 'student_wallet', 'institution', 'block_number', 'processed']
    list_filter = ['processed', 'institution']
    search_fields = ['credential_id', 'student_wallet', 'fingerprint']


@admin.register(CredentialRevokedEvent)
class CredentialRevokedEventAdmin(admin.ModelAdmin):
    list_display = ['credential_id', 'revoked_by', 'revoked_at', 'block_number', 'processed']
    list_filter = ['processed']
    search_fields = ['credential_id']


@admin.register(IndexerState)
class IndexerStateAdmin(admin.ModelAdmin):
    list_display = ['key', 'last_processed_block', 'updated_at']
    readonly_fields = ['updated_at']


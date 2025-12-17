from django.contrib import admin
from .models import Credential


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = ['credential_id', 'student_wallet', 'institution', 'issued_at', 'revoked', 'is_valid']
    list_filter = ['revoked', 'institution', 'issued_at']
    search_fields = ['credential_id', 'student_wallet', 'fingerprint']
    readonly_fields = ['credential_id', 'created_at', 'updated_at']
    
    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True


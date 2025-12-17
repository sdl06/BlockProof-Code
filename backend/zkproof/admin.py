from django.contrib import admin
from .models import ZKProof, ZKProofVerification, ZKCircuit


@admin.register(ZKProof)
class ZKProofAdmin(admin.ModelAdmin):
    list_display = ['id', 'credential', 'proof_type', 'is_valid', 'verified_at', 'created_at']
    list_filter = ['proof_type', 'is_valid', 'created_at']
    search_fields = ['credential__credential_id', 'proof_ipfs_hash', 'circuit_hash']
    readonly_fields = ['created_at', 'updated_at', 'verified_at']


@admin.register(ZKProofVerification)
class ZKProofVerificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'proof', 'verification_result', 'verification_time', 'created_at']
    list_filter = ['verification_result', 'created_at']
    search_fields = ['proof__credential__credential_id', 'verifier_address']
    readonly_fields = ['created_at']


@admin.register(ZKCircuit)
class ZKCircuitAdmin(admin.ModelAdmin):
    list_display = ['name', 'circuit_type', 'version', 'is_active', 'created_at']
    list_filter = ['circuit_type', 'is_active', 'created_at']
    search_fields = ['name', 'circuit_hash']
    readonly_fields = ['circuit_hash', 'created_at', 'updated_at']











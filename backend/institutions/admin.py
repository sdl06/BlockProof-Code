from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Institution


class InstitutionInline(admin.StackedInline):
    """Inline admin for Institution linked to User."""
    model = Institution
    can_delete = False
    verbose_name_plural = 'Institution Profile'
    fields = ['address', 'name', 'is_active', 'api_key']


class CustomUserAdmin(UserAdmin):
    """Extend UserAdmin to include Institution profile."""
    inlines = (InstitutionInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'is_active', 'user', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'address', 'user__username']
    readonly_fields = ['api_key']
    
    def save_model(self, request, obj, form, change):
        """Auto-generate API key if not set."""
        if not obj.api_key:
            obj.generate_api_key()
        super().save_model(request, obj, form, change)


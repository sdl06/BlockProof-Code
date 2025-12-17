from rest_framework import serializers
from .models import Institution


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = [
            'address',
            'name',
            'is_active',
            'created_at',
            'last_updated_at',
        ]


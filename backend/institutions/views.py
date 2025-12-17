from rest_framework import viewsets
from .models import Institution
from .serializers import InstitutionSerializer


class InstitutionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Institution.objects.filter(is_active=True)
    serializer_class = InstitutionSerializer
    lookup_field = 'address'


"""
URL configuration for blockproof_backend project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from credentials import verification_views

# Import test endpoints first
from blockproof_backend.test_simple import test_simple
from institutions.health_check import health_check as institutions_health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    # Test endpoints at the top
    path('test-simple/', test_simple, name='test_simple'),
    path('api/institutions/health/', institutions_health_check, name='institutions_health_check'),
    path('api/health/', institutions_health_check, name='api_health_check'),
    path('health/', institutions_health_check, name='health_check'),
    # Other API endpoints
    path('api/credentials/', include('credentials.urls')),
    path('api/institutions/', include('institutions.urls')),
    path('api/blockchain/', include('blockchain.urls')),
    path('api/zkproof/', include('zkproof.urls')),
    # Public verification endpoint (accessible without /api prefix for share links)
    path('verify/<int:credential_id>/<str:fingerprint>/', verification_views.verify_from_link, name='verify_from_link'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

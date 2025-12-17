"""
URL configuration for blockproof_backend project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from credentials import verification_views

urlpatterns = [
    path('admin/', admin.site.urls),
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


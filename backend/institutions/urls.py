from django.urls import path
from blockproof_backend.router import NoFormatSuffixRouter
from . import views
from .test_endpoint import test_endpoint
from .health_check import health_check

# Register custom routes FIRST to avoid conflicts with router
# Django matches URLs in order, so these must come before the router
urlpatterns = [
    path('health/', health_check, name='health_check'),  # Health check - no auth required
    path('test/', test_endpoint, name='test_endpoint'),  # Temporary test endpoint
    path('register/', views.register_institution, name='register_institution'),
]

# Create router and register ViewSet
router = NoFormatSuffixRouter()
# Register with empty string - this creates:
# - List route: GET /api/institutions/ 
# - Detail route: GET /api/institutions/<address>/ (where address matches 0x[a-fA-F0-9]{40})
# - Action routes: GET /api/institutions/me/ (from @action decorator)
router.register(r'', views.InstitutionViewSet, basename='institution')

# Add router URLs AFTER custom routes (so custom routes are checked first)
urlpatterns += router.urls


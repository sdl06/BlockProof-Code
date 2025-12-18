from django.urls import path
from blockproof_backend.router import NoFormatSuffixRouter
from . import views
from . import verification_views

# Register custom paths FIRST to avoid conflicts with router
# Django matches URLs in order, so these must come before the router
urlpatterns = [
    # Public verification endpoint (no auth required)
    path('verify/<int:credential_id>/<str:fingerprint>/', verification_views.verify_from_link, name='verify_from_link'),
    path('verify-upload/', verification_views.verify_uploaded_document, name='verify_uploaded_document'),
    # Student verification request (public endpoint)
    path('student-verify/', views.student_verify, name='student_verify'),
]

# Create router and register ViewSet
router = NoFormatSuffixRouter()
router.register(r'', views.CredentialViewSet, basename='credential')

# Add router URLs AFTER custom routes (so custom routes are checked first)
urlpatterns += router.urls


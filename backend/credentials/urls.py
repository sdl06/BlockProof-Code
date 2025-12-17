from django.urls import path
from blockproof_backend.router import NoFormatSuffixRouter
from . import views
from . import verification_views

router = NoFormatSuffixRouter()
router.register(r'', views.CredentialViewSet, basename='credential')

urlpatterns = router.urls + [
    # Public verification endpoint (no auth required)
    path('verify/<int:credential_id>/<str:fingerprint>/', verification_views.verify_from_link, name='verify_from_link'),
    path('verify-upload/', verification_views.verify_uploaded_document, name='verify_uploaded_document'),
]


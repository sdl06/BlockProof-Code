from django.urls import path
from blockproof_backend.router import NoFormatSuffixRouter
from . import views

router = NoFormatSuffixRouter()
router.register(r'', views.InstitutionViewSet, basename='institution')

urlpatterns = router.urls


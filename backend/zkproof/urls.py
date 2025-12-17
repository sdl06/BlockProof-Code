from django.urls import path
from blockproof_backend.router import NoFormatSuffixRouter
from . import views

router = NoFormatSuffixRouter()
router.register(r'proofs', views.ZKProofViewSet, basename='zkproof')
router.register(r'circuits', views.ZKCircuitViewSet, basename='zkcircuit')

urlpatterns = router.urls + [
    path('status/', views.zkproof_status, name='zkproof_status'),
]


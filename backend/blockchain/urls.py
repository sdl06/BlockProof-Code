from django.urls import path
from . import views

urlpatterns = [
    path('verify/', views.verify_credential, name='verify_credential'),
    path('status/<int:credential_id>/', views.credential_status, name='credential_status'),
    path('tx/<str:tx_hash>/', views.transaction_receipt, name='transaction_receipt'),
]


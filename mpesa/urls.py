from django.urls import path
from . import views

app_name = 'mpesa'

urlpatterns = [
    path('initiate-payment/', views.initiate_deposit_payment, name='initiate_payment'),
    path('callback/', views.mpesa_callback, name='callback'),
    path('query-status/<uuid:request_id>/', views.query_transaction_status, name='query_status'),
]

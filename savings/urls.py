from django.urls import path

from . import views

app_name = 'savings'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('deposit/new/', views.deposit_new, name='deposit_new'),
    path('deposit/<int:pk>/confirm/', views.deposit_confirm, name='deposit_confirm'),
    path('deposit-page/', views.deposit_page, name='deposit_page'),
    path('api/initiate-stk-push/', views.initiate_stk_push, name='initiate_stk_push'),
    path('api/submit-approval-request/', views.submit_approval_request, name='submit_approval_request'),
]

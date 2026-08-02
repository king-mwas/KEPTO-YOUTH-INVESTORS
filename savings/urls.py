from django.urls import path

from . import views

app_name = 'savings'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('deposit/new/', views.deposit_new, name='deposit_new'),
    path('deposit/<int:pk>/confirm/', views.deposit_confirm, name='deposit_confirm'),
]

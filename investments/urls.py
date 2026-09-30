from django.urls import path

from . import views

app_name = 'investments'

urlpatterns = [
    path('', views.home, name='home'),
    path('invest/<slug:slug>/', views.invest, name='invest'),
]

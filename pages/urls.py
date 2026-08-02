from django.urls import path

from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('entrepreneurship/', views.entrepreneurship, name='entrepreneurship'),
    path('savings/', views.savings, name='savings'),
    path('contact/', views.contact, name='contact'),
]

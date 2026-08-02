from django.urls import path

from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('members/pending/', views.members_pending, name='members_pending'),
    path('deposits/pending/', views.deposits_pending, name='deposits_pending'),
    path('members/search/', views.member_search, name='member_search'),
    path('settings/', views.site_settings, name='site_settings'),
]

from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home_view, name='home_view'),
    path('dashboard/', views.dashboard_view, name='dashboard_view'),
    path('browse/', views.browse_view, name='browse_view')
]
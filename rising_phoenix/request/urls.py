from django.urls import path

from . import views

app_name = 'request'

urlpatterns = [
    path('', views.request_list_view, name='request_list_view'),
    path('create/', views.request_create_view, name='request_create_view'),
    path('api/refine-text/', views.refine_request_view, name='refine_request_view'),
    path('debug/ai-config/', views.check_ai_config_view, name='check_ai_config_view'),
]
from django.urls import path
from . import views
app_name = "workshop"
urlpatterns = [
    path('create/', views.create_workshop_view, name='create_workshop_view'),
    path('upload-portfolio/', views.upload_portfolio_view, name='upload_portfolio_view'),
    path('projects/create/', views.create_project_view, name='create_project_view'),
    path('projects/<int:project_id>/upload-images/', views.upload_project_images_view, name='upload_project_images_view'),
    path('projects/<int:project_id>/', views.project_detail_view, name='project_detail_view'),
    path('artisan/<int:artisan_id>/projects/', views.projects_list_view, name='projects_list_view'),
    path('artisan/<int:artisan_id>/portfolio/', views.portfolio_list_view, name='portfolio_list_view'),
    path('artisan/<int:artisan_id>/closed-requests/', views.closed_requests_view, name='closed_requests_view'),
    path('artisans/', views.artisans_list_view, name='artisans_list_view'),
    path('artisan/<int:artisan_id>/', views.workshop_detail_view, name='workshop_detail_view'),
]

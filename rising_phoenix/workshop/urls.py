from django.urls import path
from . import views
app_name = "workshop"
urlpatterns = [
    path('create/', views.create_workshop_view, name='create_workshop_view'),
    path('artisan/<int:artisan_id>/', views.workshop_detail_view, name='workshop_detail_view'),
]
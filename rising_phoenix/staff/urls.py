from django.urls import path
from . import views
app_name = "staff"


urlpatterns = [
    path("dashboard/", views.staff_dashboard_view, name="staff_dashboard_view"),
    path("users/<int:user_id>/ban/", views.ban_user_view, name="ban_user_view"),
    path("artisans/<int:user_id>/ban/", views.ban_artisan_view, name="ban_artisan_view"),
    path("artisans/<int:user_id>/feature/", views.feature_artisan_view, name="feature_artisan_view"),
    path("artisans/<int:user_id>/verify/", views.verify_artisan_view, name="verify_artisan_view"),
]


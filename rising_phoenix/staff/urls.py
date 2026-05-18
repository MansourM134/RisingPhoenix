from django.urls import path
from . import views
app_name = "staff"


urlpatterns = [
    path("dashboard/", views.staff_dashboard_view, name="staff_dashboard_view"),
    path("profile/", views.staff_profile_view, name="staff_profile_view"),
    path("profile/update/", views.update_staff_profile_view, name="update_staff_profile_view"),
    path("users/<int:user_id>/ban/", views.ban_user_view, name="ban_user_view"),
    path("artisans/<int:user_id>/ban/", views.ban_artisan_view, name="ban_artisan_view"),
    path("artisans/<int:user_id>/feature/", views.feature_artisan_view, name="feature_artisan_view"),
    path("artisans/<int:user_id>/verify/", views.verify_artisan_view, name="verify_artisan_view"),
    path("categories/add/", views.add_category_view, name="add_category_view"),
    # Report management (staff only)
    path("reports/", views.report_list_view, name="report_list_view"),
    path("reports/<int:report_id>/resolve/", views.resolve_report_view, name="resolve_report_view"),
]


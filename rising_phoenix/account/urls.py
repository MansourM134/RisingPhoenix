from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('signup/', views.signup_view, name='signup_view'),
    path('login/', views.login_view, name="login_view"),
    path('logout/', views.logout_view, name='logout_view'),
    path('artisan_signup/', views.artisan_signup_view, name='artisan_signup_view'),

    path('dashboard/', views.artisan_dashboard_view, name='artisan_dashboard_view'),`
    path('profile/<user_name>', views.profile_view, name='profile_view'),
    path('profile/<user_name>/update', views.update_profile_view, name='update_profile_view')
]
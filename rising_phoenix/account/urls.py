from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'account'

urlpatterns = [
    path('signup/', views.signup_view, name='signup_view'),
    path('login/', views.login_view, name="login_view"),
    path('logout/', views.logout_view, name='logout_view'),
    path('artisan_signup/', views.artisan_signup_view, name='artisan_signup_view'),

    path('dashboard_artisan/', views.artisan_dashboard_view, name='artisan_dashboard_view'),
    path('profile/<user_name>', views.profile_view, name='profile_view'),
    path('profile/<user_name>/update', views.update_profile_view, name='update_profile_view'),
    path('profile/<user_name>/verified_phone', views.verify_phone_view, name='verify_phone_view'),
    path('account/profile/<str:user_name>/send-phone-verification/', views.send_phone_verification_view, name='send_phone_verification'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='account/password_reset.html',
            email_template_name='account/password_reset_email.html',
            subject_template_name='account/password_reset_subject.txt',
            success_url='/account/password-reset/done/'
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='account/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='account/password_reset_confirm.html',
            success_url='/account/reset/done/'
        ),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='account/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]
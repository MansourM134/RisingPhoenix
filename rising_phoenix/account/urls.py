from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'account'

urlpatterns = [
    path('signup/', views.signup_view, name='signup_view'),
    path('login/', views.login_view, name="login_view"),
    path('logout/', views.logout_view, name='logout_view'),
    path('artisan_signup/', views.artisan_signup_view, name='artisan_signup_view'),
    path('dashboard-artisan/', views.artisan_revenue_dashboard_view, name='artisan_revenue_dashboard_view'),
    path('dashboard_artisan/', views.artisan_dashboard_view, name='artisan_dashboard_view'),
    path('artisan/revenue/export-pdf/', views.artisan_revenue_pdf_view, name='artisan_revenue_pdf_view'),
    path('review/submit/<int:contract_id>/', views.submit_review_view, name='submit_review_view'),
    path('review/history/', views.review_history_view, name='review_history_view'),
    path('profile/<user_name>', views.profile_view, name='profile_view'),
    path('artisan_profile/<user_name>', views.artisan_profile_view, name='artisan_profile_view'),
    path('profile/<user_name>/update', views.update_profile_view, name='update_profile_view'),
    path('artisan_profile/<user_name>/update', views.update_artisan_profile_view, name='update_artisan_profile_view'),
    path('profile/<user_name>/verified_phone', views.verify_phone_view, name='verify_phone_view'),
    path('completed-orders/', views.completed_orders_view, name='completed_orders_view'),
    path('account/profile/<str:user_name>/send-phone-verification/', views.send_phone_verification_view, name='send_phone_verification'),
    path('artisan/connect-stripe/',views.artisan_connect_stripe_view,name='artisan_connect_stripe_view',),
    path('artisan/connect-stripe/refresh/',views.artisan_connect_stripe_refresh_view,name='artisan_connect_stripe_refresh_view',),
    path('artisan/connect-stripe/return/',views.artisan_connect_stripe_return_view,name='artisan_connect_stripe_return_view',),
    # Report & flagging (user-facing)
    path('report/<str:content_type>/<int:object_id>/', views.submit_report_view, name='submit_report_view'),
    path('my-reports/', views.my_reports_view, name='my_reports_view'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='account/password_reset.html',
            email_template_name='account/password_reset_email.html',
            html_email_template_name='account/password_reset_email_html.html',
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
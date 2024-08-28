from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('account/register/', views.RegisterView.as_view(), name='register'),
    path('account/login/', views.LoginView.as_view(), name='login'),
    path('account/verify/', views.VerifyAccountView.as_view(), name='verify-account'),
    path('account/verify/resend/', views.ResendVerificationEmailView.as_view(), name='resend-verification'),
    path('account/details/', views.UserDetailsView.as_view(), name='user-details-and-update'), # can use GET and PATCH requests
    path('account/email/change/', views.ChangeEmailView.as_view(), name='change-email'),
    path('account/password/change/', views.ChangePasswordView.as_view(), name='change-password'),
    path('account/password/request-reset/', views.RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('account/password/request-reset/verify/', views.VerifyPasswordResetView.as_view(), name='verify-password-reset'),
    path('account/password/reset/', views.PasswordResetView.as_view(), name='password-reset'),
    path('account/logout/', views.LogoutView.as_view(), name='logout'),
    path('account/delete/', views.DeleteAccountView.as_view(), name='delete-account'),
    
    # Google auth
    path('account/google/continue/', views.GoogleAuthRedirect.as_view(), name='continue-with-google'),
]

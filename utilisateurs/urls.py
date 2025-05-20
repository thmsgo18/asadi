from django.urls import path
from utilisateurs import views
from utilisateurs.views import ResetPasswordView
from django.contrib.auth import views as auth_views


urlpatterns = [

    path('', views.connexion, name='connexion'),

    path('inscription/', views.inscription, name='inscription'),
    path('password-reset/', ResetPasswordView.as_view(), name='password_reset'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='reset_password_complete.html'),name='password_reset_complete'),
path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='reset_password_confirm.html'), name='password_reset_confirm'),
]

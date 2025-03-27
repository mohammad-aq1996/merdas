from django.urls import path
from .views import *


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('admin-change-password/', AdminChangePasswordView.as_view(), name='admin-change-password'),
    path('captcha/', GenerateCaptchaView.as_view(), name='captcha'),

    path('permissions/', PermissionView.as_view(), name='permissions'),

    path('role/', RoleView.as_view(), name='role'),
    path('role/<int:pk>/', RoleDetailView.as_view(), name='roles'),

    path('group/', GroupView.as_view(), name='group'),
    path('group/<int:pk>/', GroupDetailView.as_view(), name='groups'),
]
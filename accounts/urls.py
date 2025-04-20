from django.urls import path
from .views import *


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('admin-change-password/', AdminChangePasswordView.as_view(), name='admin-change-password'),
    path('captcha/', GenerateCaptchaView.as_view(), name='captcha'),

    path('permissions/', PermissionView.as_view(), name='permissions'),

    path('role/', RoleView.as_view(), name='role'),
    path('role/<int:pk>/', RoleDetailView.as_view(), name='roles'),

    path('group/', GroupView.as_view(), name='group'),
    path('group/<int:pk>/', GroupDetailView.as_view(), name='groups'),

    path('users/', UserListView.as_view(), name='users'),
    path('user/<int:pk>/', UserDetailView.as_view(), name='users'),
    path('attempt/', LoginAttemptsView.as_view(), name='attempt'),

    path('ill/username/', IllUsernameView.as_view(), name='ill-username'),
    path('ill/username/<int:pk>/', IllUsernameDetailView.as_view(), name='ill-username-detail'),

    path('ill/password/', IllPasswordView.as_view(), name='ill-password'),
    path('ill/password/<int:pk>/', IllPasswordDetailView.as_view(), name='ill-password-detail'),

    path('unblock/login/', UnblockLoginView.as_view(), name='unblock-login'),
    path('org-groups/<int:pk>/', OrgGroupsListView.as_view(), name='org-groups'),

    path('same-group-users/', SameGroupUsersView.as_view(), name='same-group-users'),
]
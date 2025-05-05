from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('admin-change-password/', AdminChangePasswordView.as_view(), name='admin-change-password'),
    path('captcha/', GenerateCaptchaView.as_view(), name='captcha'),

    path('permissions/', PermissionView.as_view(), name='permissions'),

    path('role/', RoleView.as_view(), name='role'),
    path('role/<uuid:pk>/', RoleDetailView.as_view(), name='roles'),

    path('group/', GroupView.as_view(), name='group'),
    path('group/<uuid:pk>/', GroupDetailView.as_view(), name='groups'),

    path('users/', UserListView.as_view(), name='users'),
    path('user/<uuid:pk>/', UserDetailView.as_view(), name='users'),
    path('attempt/', LoginAttemptsView.as_view(), name='attempt'),

    path('ill/username/', IllUsernameView.as_view(), name='ill-username'),
    path('ill/username/<uuid:pk>/', IllUsernameDetailView.as_view(), name='ill-username-detail'),

    path('ill/password/', IllPasswordView.as_view(), name='ill-password'),
    path('ill/password/<uuid:pk>/', IllPasswordDetailView.as_view(), name='ill-password-detail'),

    path('unblock/login/', UnblockLoginView.as_view(), name='unblock-login'),
    path('org-groups/<uuid:pk>/', OrgGroupsListView.as_view(), name='org-groups'),

    path('same-group-users/', SameGroupUsersView.as_view(), name='same-group-users'),

    path('block/<uuid:user_id>/', AdminBlockUserView.as_view(), name='admin-block'),


    path("organization-types/", OrganizationTypeAPI.as_view(), name="organization-types"),
    path("organization-types/<uuid:pk>/", OrganizationTypeDetailAPI.as_view(), name="organization-types-detail"),
    path("simple-organization/", OrganizationSimpleView.as_view(), name="simple-organization"),
    path("organizations/", OrganizationAPI.as_view(), name="organizations"),
    path("organizations/<uuid:org_id>/", OrganizationDetailAPI.as_view(), name="organization-detail"),
]
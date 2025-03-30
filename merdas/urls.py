from django.urls import path
from .views import *


urlpatterns = [
    path("organization-types/", OrganizationTypeAPI.as_view(), name="organization-types"),
    path("organization-types/<int:pk>/", OrganizationTypeDetailAPI.as_view(), name="organization-types-detail"),
    path("organizations/", OrganizationAPI.as_view(), name="organizations"),
    path("organizations/<int:org_id>/", OrganizationDetailAPI.as_view(), name="organization-detail"),
]
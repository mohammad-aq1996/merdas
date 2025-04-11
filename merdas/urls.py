from django.urls import path
from .views import *


urlpatterns = [
    path("organization-types/", OrganizationTypeAPI.as_view(), name="organization-types"),
    path("organization-types/<int:pk>/", OrganizationTypeDetailAPI.as_view(), name="organization-types-detail"),
    path("organizations/", OrganizationAPI.as_view(), name="organizations"),
    path("organizations/<int:org_id>/", OrganizationDetailAPI.as_view(), name="organization-detail"),

    path('standard/', StandardListCreateView.as_view(), name='standard-list'),
    path('standard/<int:pk>/', StandardDetailView.as_view(), name='standard-detail'),

    path('sr/', SRListCreateView.as_view(), name='sr-list'),
    path('sr/<int:pk>/', SRDetailView.as_view(), name='sr-detail'),

    path('fr/', FRListCreateView.as_view(), name='fr-list'),
    path('fr/<int:pk>/', FRDetailView.as_view(), name='fr-detail'),

    path("questions/", QuestionListCreateView.as_view(), name="question-list"),
    path("questions/<int:pk>", QuestionDetailView.as_view(), name="question-detail"),

    path('assessments/', AssessmentListCreateView.as_view(), name="assessment-list"),
    path('assessments/<int:pk>/', AssessmentDetailView.as_view(), name="assessment-detail"),

    path('response/', SubmitAssessmentResponsesAPIView.as_view(), name="response-list"),


]
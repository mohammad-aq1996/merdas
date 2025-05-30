from django.urls import path
from .views import *


urlpatterns = [
    path('standard/', StandardListCreateView.as_view(), name='standard-list'),
    path('standard/<uuid:pk>/', StandardDetailView.as_view(), name='standard-detail'),

    path('sr/', SRListCreateView.as_view(), name='sr-list'),
    path('sr/<uuid:pk>/', SRDetailView.as_view(), name='sr-detail'),

    path('fr/', FRListCreateView.as_view(), name='fr-list'),
    path('fr/<uuid:pk>/', FRDetailView.as_view(), name='fr-detail'),

    path("questions/", QuestionListCreateView.as_view(), name="question-list"),
    path("questions/<uuid:pk>", QuestionDetailView.as_view(), name="question-detail"),

    path('questions-by-fr-sr/', QuestionsGroupedByFRSRView.as_view(), name="questions-by-fr-sr"),

    path('assessments/', AssessmentCreateView.as_view(), name='assessment-create'),
    path('assessments/<uuid:pk>/', AssessmentUpdateView.as_view(), name='assessment-update'),

    path('questions/upload-csv-by-title/', QuestionCSVUploadByTitleView.as_view(), name='upload_questions_by_title'),
    path('questions/template-csv/', QuestionCSVTemplateDownloadView.as_view(), name='download_questions_csv_template')


]
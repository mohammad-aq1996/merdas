from django.urls import path
from .views import *
from assets.csv_import.views import *

urlpatterns = [
    path('attribute/category/', AttributeCategoryListCreateView.as_view(), name='attribute_category_list_create'),
    path('attribute/category/<uuid:pk>/', AttributeCategoryDetailView.as_view(), name='attribute_category_detail'),

    path('attribute/', AttributeListCreateView.as_view(), name='attribute_list_create'),
    path('attribute/<uuid:pk>/', AttributeDetailView.as_view(), name='attribute_detail'),

    path('', AssetListCreateView.as_view(), name='asset_list_create'),
    path('<uuid:pk>/', AssetDetailView.as_view(), name='asset_detail'),

    path('attribute/list/', AssetAttributesListView.as_view(), name='asset_attribute_list_create'),

    path('relation/', RelationListCreateView.as_view(), name='relation_list_create'),
    path('relation/<uuid:pk>/', RelationDetailView.as_view(), name='relation_detail'),

    path('attribute/value/<uuid:unit_id>/', AssetAttributeValueView.as_view(), name='asset_attribute_value_list_create'),

    path('units/', AssetUnitCreateAPIView.as_view()),  # POST → ساخت یک نمونه + EAV

    path('<uuid:asset_id>/units/', AssetUnitCreateAPIView.as_view()),  # POST → ساخت یک نمونه + EAV

    path('list-unit-count/', AssetListWithUnitCountAPIView.as_view()),

    path('unit/<uuid:unit_id>/', AssetUnitUpdateAPIView.as_view()),


    path('csv/rows/all/', CsvRowsView.as_view()),
    path('csv/rows/edited/', CsvApplyEditsView.as_view()),
    path('csv/upload/preview/', CsvUploadView.as_view(), name='csv_upload'),
    path('csv/mapping/', CsvMappingView.as_view(), name='csv_mapping'),
    # path('csv/commit/', CsvCommitView.as_view(), name='csv_commit'),
    path('csv/commit/', CommitImportAPIView.as_view(), name='csv_commit'),
    path('csv/issues/<uuid:pk>/', CsvImportIssuesAPIView.as_view()),

    path('generate-csv/', GenerateTemplateCSVAPIView.as_view()),
    # path('commit/', CommitImportAPIView.as_view()),
]
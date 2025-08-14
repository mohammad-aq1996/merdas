from django.urls import path
from .views import *


urlpatterns = [
    path('attribute/category/', AttributeCategoryListCreateView.as_view(), name='attribute_category_list_create'),
    path('attribute/category/<uuid:pk>/', AttributeCategoryDetailView.as_view(), name='attribute_category_detail'),

    path('attribute/', AttributeListCreateView.as_view(), name='attribute_list_create'),
    path('attribute/<uuid:pk>/', AttributeDetailView.as_view(), name='attribute_detail'),

    path('', AssetListCreateView.as_view(), name='asset_list_create'),
    path('<uuid:pk>/', AssetDetailView.as_view(), name='asset_detail'),
]
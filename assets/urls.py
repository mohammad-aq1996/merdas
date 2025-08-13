from django.urls import path
from .views import *


urlpatterns = [
    path('attribute/category/', AttributeCategoryListCreateView.as_view(), name='attribute_category_list_create'),
    path('attribute/category/<uuid:pk>/', AttributeCategoryDetailView.as_view(), name='attribute_category_detail'),


]
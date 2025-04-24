from django.urls import path
from .views import LogView

urlpatterns = [
    path('event-logs/', LogView.as_view(), name='logs'),
]
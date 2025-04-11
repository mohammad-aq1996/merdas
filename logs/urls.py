from django.urls import path
from .views import LogView, LogEntryView

urlpatterns = [
    path('event-logs/', LogView.as_view(), name='logs'),
    path('log-entry/', LogEntryView.as_view(), name='log-entry'),
]
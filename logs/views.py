from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from core.utils import CustomResponse
from core.persian_response import get_all_data
from .models import *
from auditlog.models import LogEntry


class LogEntrySerializer(serializers.ModelSerializer):
    actor = serializers.StringRelatedField()
    timestamp = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = LogEntry
        fields = [
            'id',
            'actor',
            'action',
            'remote_addr',
            'timestamp',
            'content_type',
            'object_id',
            'changes',
            'additional_data',
        ]

class LogEntryView(APIView):
    queryset = LogEntry.objects.all()

    def get(self, request):
        qs = LogEntry.objects.all()
        serializer = LogEntrySerializer(qs, many=True)
        return CustomResponse.success(get_all_data(), serializer.data)


class LogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = EventLog
        fields = '__all__'

    def get_user(self, obj):
        return obj.user.username if obj.user else None


class LogView(APIView):
    queryset = EventLog.objects.all()

    def get(self, request):
        logs = EventLog.objects.all().order_by('-created_at')
        serializer = LogSerializer(logs, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)
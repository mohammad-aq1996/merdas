from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from core.utils import CustomResponse
from core.persian_response import get_all_data
from .models import *


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventLog
        fields = '__all__'


class LogView(APIView):
    queryset = EventLog.objects.all()

    def get(self, request):
        logs = EventLog.objects.all()
        serializer = LogSerializer(logs, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)
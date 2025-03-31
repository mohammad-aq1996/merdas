from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from core.utils import CustomResponse
from .models import *


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventLog
        fields = '__all__'


class LogView(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        logs = EventLog.objects.all()
        serializer = LogSerializer(logs, many=True)
        return CustomResponse.success(serializer.data)
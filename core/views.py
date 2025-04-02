from rest_framework.views import APIView
from .utils import CustomResponse
from .persian_response import *
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import Settings
from rest_framework import serializers


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = ('id', 'config')


class SettingsAPIView(APIView):
    queryset = Settings.objects.all()

    @extend_schema(responses=SettingsSerializer)
    def get(self, request):
        settings = Settings.objects.filter(id=1).first()
        serializer = SettingsSerializer(settings)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        examples=[
            OpenApiExample(
                name="نمونه تنظیمات",
                value={
                        "PASSWORD_HISTORY_LIMIT": 5,
                        "MAX_FAILED_LOGIN_ATTEMPTS": 5,
                        "ACCOUNT_LOCKOUT_TIME": 30,
                        "PASSWORD_EXPIRATION_DAYS": 90,
                },
            )
        ],
        responses=SettingsSerializer,
    )
    def put(self, request):
        settings, created = Settings.objects.get_or_create(id=1)
        data = request.data

        if not isinstance(data, dict):
            return CustomResponse.error(message="فرمت داده وارد شده صحیح نمیباشد")

        # آپدیت تنظیمات موجود
        for key, value in data.items():
            settings.config[key] = value

        settings.save()
        return CustomResponse.success(message=update_data(), data=settings.config)


# config = {"PASSWORD_HISTORY_LIMIT": 5 ,"MAX_FAILED_LOGIN_ATTEMPTS": 5 ,"ACCOUNT_LOCKOUT_MINUTES": 30 ,"PASSWORD_EXPIRATION_DAYS": 90}

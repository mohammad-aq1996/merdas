from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from .models import User
from .serializers import (UserSerializer, LoginSerializer, ChangePasswordSerializer, AdminChangePasswordSerializer, )
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAdminUser
import random
import string
import io
from django.core.cache import cache
from django.http import HttpResponse
from PIL import Image, ImageDraw, ImageFont
from core.utils import get_anonymous_cache_key, CustomResponse


class RegisterView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(request=UserSerializer, responses=UserSerializer)
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return CustomResponse.success("ثبت نام با موفقیت انجام شد", data={"user": user.id}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(request=LoginSerializer, responses=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return CustomResponse.success({
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })


class ChangePasswordView(APIView):
    @extend_schema(request=ChangePasswordSerializer, responses=ChangePasswordSerializer)
    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success("رمز عبور با موفقیت تغییر کرد.")


class AdminChangePasswordView(APIView):
    permission_classes = [IsAdminUser]  # فقط ادمین‌ها و سوپریوزرها دسترسی دارند

    @extend_schema(request=AdminChangePasswordSerializer, responses=AdminChangePasswordSerializer)
    def put(self, request):
        serializer = AdminChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response("رمز عبور کاربر با موفقیت تغییر کرد.")


class GenerateCaptchaView(APIView):
    permission_classes = (AllowAny, )

    def get(self, request):
        captcha_text = ''.join(random.choices((string.digits + string.ascii_lowercase) , k=7))

        captcha_key = get_anonymous_cache_key(request)
        cache.set(captcha_key, captcha_text, timeout=300)
        img = Image.new('RGB', (150, 40), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 25)
        except IOError:
            font = ImageFont.load_default()

        draw.text((20, 5), captcha_text, font=font, fill=(0, 0, 0))

        # ذخیره تصویر در حافظه
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        return HttpResponse(img_io, content_type="image/png")
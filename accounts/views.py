from django.contrib.auth.models import Permission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from .models import User, Role
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAdminUser
import random
import string
import io
from django.core.cache import cache
from django.http import HttpResponse
from PIL import Image, ImageDraw, ImageFont
from core.utils import get_anonymous_cache_key, CustomResponse
from .serializers import (UserSerializer, LoginSerializer, ChangePasswordSerializer, AdminChangePasswordSerializer,
                          PermissionSerializer, RoleSerializer, RoleCreateUpdateSerializer)


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


class PermissionView(APIView):
    permission_classes = (IsAdminUser, )

    @extend_schema(request=PermissionSerializer, responses=PermissionSerializer)
    def get(self, request):
        permissions = Permission.objects.all()
        serializer = PermissionSerializer(permissions, many=True)
        return CustomResponse.success(message=serializer.data)


class RoleView(APIView):
    permission_classes = (IsAdminUser, )

    @extend_schema(request=RoleSerializer, responses=RoleSerializer)
    def get(self, request, pk=None):
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return CustomResponse.success(message=serializer.data)

    @extend_schema(request=RoleCreateUpdateSerializer, responses=RoleCreateUpdateSerializer)
    def post(self, request):
        serializer = RoleCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success("نقش با موفقیت ساخته شد")


class RoleDetailView(APIView):
    permission_classes = (IsAdminUser, )

    @extend_schema(request=RoleSerializer, responses=RoleSerializer)
    def get(self, request, pk=None):
        try:
            role = Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return CustomResponse.error(message="نقش مورد نظر یافت نشد")

        serializer = RoleSerializer(role)
        return CustomResponse.success(message=serializer.data)

    @extend_schema(request=RoleCreateUpdateSerializer, responses=RoleCreateUpdateSerializer)
    def put(self, request, pk=None):
        try:
            instance = Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return CustomResponse.error(message="نقش مورد نظر یافت نشد")
        serializer = RoleCreateUpdateSerializer(instance=instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(message=serializer.data)

    def delete(self, request, pk=None):
        try:
            instance = Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return CustomResponse.error(message="نقش مورد نظر یافت نشد")
        instance.delete()
        return CustomResponse.success("نقش مورد نظر با موفقیت حذف شد")




















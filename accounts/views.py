from django.contrib.auth.models import Permission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from .models import User, Role, UserGroup
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
import random
import string
import io
from django.core.cache import cache
from django.http import HttpResponse
from PIL import Image, ImageDraw, ImageFont
from core.utils import get_anonymous_cache_key, CustomResponse
from .serializers import *
from logs.utils import log_event
from logs.models import EventLog
from core.persian_response import get_all_data, get_single_data, create_data, update_data, delete_data
from merdas.models import Organization


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=LogoutSerializer)
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()  # توکن را باطل می‌کند
            log_event(request.user, EventLog.EventTypes.LOGOUT, request=request)
            return CustomResponse.success("خروج موفقیت‌آمیز بود.")
        except Exception as e:
            log_event(request.user, EventLog.EventTypes.LOGOUT, request=request, success=False)
            return CustomResponse.error("توکن نامعتبر است.")


class RegisterView(APIView):
    queryset = User.objects.all()

    @extend_schema(request=UserSerializer, responses=UserGetSerializer)
    def post(self, request):
        serializer = UserSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        output_serializer = UserGetSerializer(instance)
        return CustomResponse.success("ثبت نام کاربر جدید با موفقیت انجام شد", data=output_serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(request=LoginSerializer, responses=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        return CustomResponse.success(message="ورود موفق",
                                      data={
                                            'access': str(refresh.access_token),
                                            'refresh': str(refresh),
                                            'must_change_password': user.must_change_password(),
                                            'permissions': str([obj.codename for obj in user.group.roles.all()[0].permissions.all()]) if user.group else None,
                                            'organization': str(user.organization.name) if user.organization else None,
                                            'fullname': str(user.get_full_name()) if user.get_full_name() else None,
                                            'is_admin': str(True) if user.is_admin or user.is_superuser else None,
                                        }
                                      )


class ChangePasswordView(APIView):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=ChangePasswordSerializer, responses=ChangePasswordSerializer)
    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            new_password = serializer.validated_data['new_password']
            request.user.update_password(new_password)  # حالا این متد، چک و ذخیره رو خودش انجام میده
        except ValueError as e:
            return CustomResponse.error(message="تغییر رمز عبور ناموفق", errors=str(e))
        return CustomResponse.success("رمز عبور با موفقیت تغییر کرد.")


class AdminChangePasswordView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=AdminChangePasswordSerializer, responses=AdminChangePasswordSerializer)
    def put(self, request):
        serializer = AdminChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success("رمز عبور کاربر با موفقیت تغییر کرد.")


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
    queryset = Permission.objects.all()

    @extend_schema(request=PermissionSerializer, responses=PermissionSerializer)
    def get(self, request):
        EXCLUDED_MODELS = [
            "session",
            "contenttype",
            "logentry",
            "group",
            "permission",
            "admin",
            "blacklistedtoken",
            "outstandingtoken",
        ]
        permissions = Permission.objects.exclude(
            content_type__model__in=EXCLUDED_MODELS
        )
        serializer = PermissionSerializer(permissions, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)


class RoleView(APIView):
    queryset = Role.objects.all()

    @extend_schema(request=RoleSerializer, responses=RoleSerializer)
    def get(self, request, pk=None):
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(request=RoleCreateUpdateSerializer, responses=RoleCreateUpdateSerializer)
    def post(self, request):
        serializer = RoleCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(message=create_data(), data=serializer.data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    queryset = Role.objects.all()

    @extend_schema(request=RoleSerializer, responses=RoleSerializer)
    def get(self, request, pk=None):
        try:
            role = Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return CustomResponse.error(message="نقش مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)

        serializer = RoleSerializer(role)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(request=RoleCreateUpdateSerializer, responses=RoleCreateUpdateSerializer)
    def put(self, request, pk=None):
        try:
            instance = Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return CustomResponse.error(message="نقش مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = RoleCreateUpdateSerializer(instance=instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(message=update_data(), data=serializer.data)

    def delete(self, request, pk=None):
        try:
            instance = Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return CustomResponse.error(message="نقش مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        instance.delete()
        return CustomResponse.success(delete_data(), status=status.HTTP_204_NO_CONTENT)


class GroupView(APIView):
    queryset = UserGroup.objects.all()

    @extend_schema(request=GroupSerializer, responses=GroupSerializer)
    def get(self, request, pk=None):
        groups = UserGroup.objects.all()
        serializer = GroupSerializer(groups, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(request=GroupCreateUpdateSerializer, responses=GroupSerializer)
    def post(self, request):
        serializer = GroupCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        output_serializer = GroupSerializer(instance)
        return CustomResponse.success(create_data(), data=output_serializer.data, status=status.HTTP_201_CREATED)


class GroupDetailView(APIView):
    queryset = UserGroup.objects.all()

    @extend_schema(request=GroupSerializer, responses=GroupSerializer)
    def get(self, request, pk=None):
        try:
            group = UserGroup.objects.get(pk=pk)
        except UserGroup.DoesNotExist:
            return CustomResponse.error(message="گروه مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)

        serializer = GroupSerializer(group)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(request=GroupCreateUpdateSerializer, responses=GroupSerializer)
    def put(self, request, pk=None):
        try:
            instance = UserGroup.objects.get(pk=pk)
        except UserGroup.DoesNotExist:
            return CustomResponse.error(message="گروه مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = GroupCreateUpdateSerializer(instance=instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer = serializer.save()
        output_serializer = GroupSerializer(serializer)
        return CustomResponse.success(message=update_data(), data=output_serializer.data)

    def delete(self, request, pk=None):
        try:
            instance = UserGroup.objects.get(pk=pk)
        except UserGroup.DoesNotExist:
            return CustomResponse.error(message="گروه مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        instance.delete()
        return CustomResponse.success(delete_data(), status=status.HTTP_204_NO_CONTENT)


class UserListView(APIView):
    queryset = User.objects.all()

    @extend_schema(request=UserGetSerializer, responses=UserGetSerializer)
    def get(self, requset):
        users = User.objects.all()
        serializer = UserGetSerializer(users, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)


class UserDetailView(APIView):
    queryset = User.objects.all()

    @extend_schema(request=UserGetSerializer, responses=UserGetSerializer)
    def get(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return CustomResponse.error("کاربر مورد نظر وجود ندارد", status=status.HTTP_404_NOT_FOUND)
        serializer = UserGetSerializer(user)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(request=USerUpdateSerializer, responses=UserGetSerializer)
    def put(self, request, pk=None):
        try:
            instance = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return CustomResponse.error("کاربر مورد نظر وجود ندارد", status=status.HTTP_404_NOT_FOUND)
        serializer = USerUpdateSerializer(instance=instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer = serializer.save()
        output_serializer = UserGetSerializer(serializer)
        return CustomResponse.success(message=update_data(), data=output_serializer.data)

    def delete(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return CustomResponse.error("کاربر مورد نظر وجود ندارد", status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return CustomResponse.success(delete_data(), status=status.HTTP_204_NO_CONTENT)


class LoginAttemptsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=LoginAttemptsSerializer)
    def get(self, request):
        qs = LoginAttempt.objects.filter(username=request.user.username)[:5]
        serializer = LoginAttemptsSerializer(qs, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)



class IllUsernameView(APIView):
    queryset = IllUsername.objects.all()

    @extend_schema(responses=IllUsernameSerializer)
    def get(self, request):
        qs = IllUsername.objects.all()
        serializer = IllUsernameSerializer(qs, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(responses=IllUsernameSerializer, request=IllUsernameSerializer)
    def post(self, request):
        serializer = IllUsernameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(message=create_data(), data=serializer.data)


class IllUsernameDetailView(APIView):
    queryset = IllUsername.objects.all()

    @extend_schema(responses=IllUsernameSerializer)
    def get(self, request, pk=None):
        try:
            instance = IllUsername.objects.get(pk=pk)
        except IllUsername.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = IllUsernameSerializer(instance=instance)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(responses=IllUsernameSerializer, request=IllUsernameSerializer)
    def put(self, request, pk=None):
        try:
            instance = IllUsername.objects.get(pk=pk)
        except IllUsername.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = IllUsernameSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(message=update_data(), data=serializer.data)

    def delete(self, request, pk=None):
        try:
            instance = IllUsername.objects.get(pk=pk)
        except IllUsername.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        instance.delete()
        return CustomResponse.success(delete_data(), status=status.HTTP_204_NO_CONTENT)


class IllPasswordView(APIView):
    queryset = IllPassword.objects.all()

    @extend_schema(responses=IllPasswordSerializer)
    def get(self, request):
        instances = self.queryset.all()
        serializer = IllPasswordSerializer(instances, many=True)
        return CustomResponse.success(
            message=get_all_data(),
            data=serializer.data
        )

    @extend_schema(
        request=IllPasswordSerializer,
        responses=IllPasswordSerializer,
    )
    def post(self, request):
        serializer = IllPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(
            message=create_data(),
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )


class IllPasswordDetailView(APIView):
    queryset = IllPassword.objects.all()

    @extend_schema(responses=IllPasswordSerializer,)
    def get(self, request, pk=None):
        try:
            instance = self.queryset.get(pk=pk)
        except IllPassword.DoesNotExist:
            return CustomResponse.error(
                message="یافت نشد",
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = IllPasswordSerializer(instance)
        return CustomResponse.success(
            message=get_single_data(),
            data=serializer.data
        )

    @extend_schema(
        request=IllPasswordSerializer,
        responses=IllPasswordSerializer,
    )
    def put(self, request, pk=None):
        try:
            instance = self.queryset.get(pk=pk)
        except IllPassword.DoesNotExist:
            return CustomResponse.error(
                message="یافت نشد",
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = IllPasswordSerializer(
            instance,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(
            message=update_data(),
            data=serializer.data
        )

    def delete(self, request, pk=None):
        try:
            instance = self.queryset.get(pk=pk)
        except IllPassword.DoesNotExist:
            return CustomResponse.error(
                message="یافت نشد",
                status=status.HTTP_404_NOT_FOUND
            )
        instance.delete()
        return CustomResponse.success(
            message=delete_data(),
            status=status.HTTP_204_NO_CONTENT
        )


class UnblockLoginView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(request=UsernameSerializer, responses=UsernameSerializer)
    def post(self, request):
        username = request.data.get("username")
        if not username:
            return CustomResponse.error("نام کاربری را وارد نمایدد")

        LoginAttempt.objects.filter(username=username).delete()
        return CustomResponse.success("رفع محدودیت کاربر با موفقیت انجام شد")


class OrgGroupsListView(APIView):
    queryset = UserGroup.objects.all()

    def get(self, request, pk):
        try:
            organization = Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        qs = organization.groups.all()
        serializer = GroupSerializer(qs, many=True)
        return CustomResponse.success(get_all_data(), data=serializer.data)

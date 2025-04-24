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
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from core.utils import get_anonymous_cache_key, CustomResponse
from .serializers import *
from logs.utils import log_event
from logs.models import EventLog
from core.persian_response import get_all_data, get_single_data, create_data, update_data, delete_data


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
        captcha_text = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
        captcha_key = get_anonymous_cache_key(request)
        cache.set(captcha_key, captcha_text, timeout=300)

        img = Image.new('RGB', (150, 50), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 30)
        except IOError:
            font = ImageFont.load_default()

        # کشیدن کاراکترها با کمی جابجایی و چرخش
        for i, char in enumerate(captcha_text):
            x = 10 + i * 20 + random.randint(-2, 2)
            y = random.randint(5, 15)
            draw.text((x, y), char, font=font, fill=(0, 0, 0))

        # نویز ساده: چند خط
        for _ in range(3):
            x1 = random.randint(0, 150)
            y1 = random.randint(0, 50)
            x2 = random.randint(0, 150)
            y2 = random.randint(0, 50)
            draw.line(((x1, y1), (x2, y2)), fill=(200, 200, 200), width=1)

        # نویز نقطه‌ای
        for _ in range(100):
            x = random.randint(0, 150)
            y = random.randint(0, 50)
            draw.point((x, y), fill=(100, 100, 100))

        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        return HttpResponse(img_io, content_type='image/png')


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


class SameGroupUsersView(APIView):
    queryset = User.objects.all()

    @extend_schema(responses=SimpleUserSerializer)
    def get(self, request):
        user = request.user
        qs = User.objects.filter(group=user.group).exclude(id=user.id).only("id", "username")
        serializer = SimpleUserSerializer(qs, many=True)
        return CustomResponse.success(get_single_data(), data=serializer.data)


class AdminBlockUserView(APIView):
    permission_classes = (IsAdminUser, )

    @extend_schema(request=AdminBlockUserSerializer)
    def patch(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return CustomResponse.error("کاربر مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)

        is_blocked = request.data.get('is_admin_blocked')
        if is_blocked is None:
            return CustomResponse.error("وارد کردن این فیلد ضروری میباشد",)

        user.is_admin_blocked = bool(is_blocked)
        user.save()
        if user.is_admin_blocked:
            log_event(request.user, EventLog.EventTypes.USER_LOCKED, request=request, description=f"کاریر {user.username} با موفقیت لاک شد")
        else:
            log_event(request.user, EventLog.EventTypes.USER_UNLOCKED, request=request, description=f"کاریر {user.username} با موفقیت آنلاک شد")
        return CustomResponse.success({
            'detail': 'وضعیت بلاک بودن کاربر با موفقیت تغییر کرد.',
            'user_id': user.id,
            'is_admin_blocked': user.is_admin_blocked
        })


class OrganizationTypeAPI(APIView):
    queryset = OrganizationType.objects.all()

    @extend_schema(responses=OrganizationTypeSerializer)
    def get(self, request, *args, **kwargs):
        types = OrganizationType.objects.all()
        serializer = OrganizationTypeSerializer(types, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(request=OrganizationTypeSerializer, responses=OrganizationSerializer)
    def post(self, request, *args, **kwargs):
        serializer = OrganizationTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success("نوع سازمان مورد نظر با موفقیت ذخیره شد", data=serializer.data)
        return CustomResponse.error(message=create_data(), errors=serializer.errors)


class OrganizationTypeDetailAPI(APIView):
    queryset = OrganizationType.objects.all()

    @extend_schema(responses=OrganizationTypeSerializer)
    def get(self, request, pk):
        try:
            qs = OrganizationType.objects.get(pk=pk)
        except OrganizationType.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationTypeSerializer(qs)
        return CustomResponse.success(get_single_data(), data=serializer.data)

    @extend_schema(responses=OrganizationTypeSerializer, request=OrganizationTypeSerializer)
    def put(self, request, pk):
        try:
            instance = OrganizationType.objects.get(pk=pk)
        except OrganizationType.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationTypeSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(message=update_data(), data=serializer.data)

    def delete(self, request, pk):
        try:
            instance = OrganizationType.objects.get(pk=pk)
        except OrganizationType.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        instance.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)


class OrganizationSimpleView(APIView):
    queryset = Organization.objects.only("id", "name")

    @extend_schema(responses=OrganizationSimpleSerializer)
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_admin or user.is_superuser:
            qs = self.queryset.all()
        elif user.organization:
            qs = user.organization.get_descendants(include_self=True)
        else:
            qs = []
        serializer = OrganizationSimpleSerializer(qs, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)


class OrganizationAPI(APIView):
    queryset = Organization.objects.all()

    @extend_schema(responses=OrganizationReadSerializer)
    def get(self, request, *args, **kwargs):
        # parent_id = request.query_params.get("parent", None)
        # if parent_id:
        #     organizations = Organization.objects.filter(parent_id=parent_id)
        # else:
        #     organizations = Organization.objects.filter(parent=None)
        user = request.user
        if user.is_admin or user.is_superuser:
            qs = self.queryset.all()
        elif user.organization:
            qs = user.organization.get_descendants(include_self=True)
        else:
            qs = []
        serializer = OrganizationReadSerializer(qs, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(responses=OrganizationReadSerializer, request=OrganizationSerializer)
    def post(self, request, *args, **kwargs):
        serializer = OrganizationSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            output_serializer = OrganizationReadSerializer(instance)
            return CustomResponse.success(create_data(), data=output_serializer.data, status=status.HTTP_201_CREATED)
        return CustomResponse.error("ذخیره سازمان ناموفق بود", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationDetailAPI(APIView):
    queryset = Organization.objects.all()

    @extend_schema(responses=OrganizationReadSerializer)
    def get(self, request, org_id, *args, **kwargs):
        user = request.user
        if user.is_admin or user.is_superuser:
            qs = self.queryset.all()
        elif user.organization:
            qs = user.organization.get_descendants(include_self=True)
        else:
            qs = []
        try:
            organization = qs.objects.get(pk=org_id)
        except Exception as e:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationReadSerializer(organization)
        return CustomResponse.success(get_single_data(), data=serializer.data)

    @extend_schema(responses=OrganizationReadSerializer, request=OrganizationSerializer)
    def put(self, request, org_id, *args, **kwargs):
        try:
            organization = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationSerializer(organization, data=request.data, partial=True)
        if serializer.is_valid():
            serializer = serializer.save()
            output_serializer = OrganizationReadSerializer(serializer)
            return CustomResponse.success(update_data(), data=output_serializer.data)
        return CustomResponse.error("بروزرسانی ناموفق", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, org_id, *args, **kwargs):
        try:
            organization = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        organization.delete()
        return CustomResponse.success(delete_data(), status=status.HTTP_204_NO_CONTENT)






from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Role, UserGroup, LoginAttempt, IllPassword, IllUsername
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from core.utils import get_anonymous_cache_key
from django.contrib.auth.models import Permission
from django.utils.timezone import now, timedelta
from logs.utils import log_event
from logs.models import EventLog
from core.models import Settings
from .encrypt import decryption


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(validators=[])

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'phone_number', 'national_number', 'organization']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, password):
        # password = decryption(password)
        if IllPassword.objects.filter(password=password).exists():
            raise serializers.ValidationError("رمز عبور غیرمجاز است")
        return password

    def validate_username(self, value):
        # username = decryption(value)
        if IllUsername.objects.filter(username=value).exists():
            raise serializers.ValidationError('نام کاربری غیرمجاز است')
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('کاربر با این نام کاربری وجود دارد')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    captcha = serializers.CharField(write_only=True)

    def validate(self, data):
        # username = decryption(data['username'])
        # password = decryption(data['password'])
        request = self.context.get("request")
        captcha_key = get_anonymous_cache_key(request)
        cached_captcha = cache.get(captcha_key)

        if not cached_captcha:
            raise serializers.ValidationError("کپچا منقضی شده است، لطفاً دوباره دریافت کنید.")

        if data["captcha"] != cached_captcha:
            raise serializers.ValidationError("کپچا اشتباه است.")

        cache.delete(captcha_key)

        failed_login_limit = Settings.get_setting("MAX_FAILED_LOGIN_ATTEMPTS", 2)

        account_lockout_time = Settings.get_setting("ACCOUNT_LOCKOUT_TIME", 2)

        login_attempt = LoginAttempt.objects.filter(username=data['username'])[:failed_login_limit]

        counter = 0

        if login_attempt and not login_attempt[0].success:
            for attempt in login_attempt:
                if not attempt.success:
                    counter += 1
                else:
                    break
        if counter >= failed_login_limit and  now() <= login_attempt[0].create + timedelta(minutes=account_lockout_time):
            raise serializers.ValidationError("حساب کاربری شما موقتا مسدود شده است")

        user = authenticate(username=data['username'], password=data['password'])

        if not user:
            LoginAttempt.objects.create(username=data['username'], ip_address=request.META['REMOTE_ADDR'], success=False)
            log_event(user, EventLog.EventTypes.LOGIN, request=request, success=False)

            raise serializers.ValidationError("نام کاربری یا رمز عبور اشتباه است.")

        LoginAttempt.objects.create(username=data['username'], ip_address=request.META['REMOTE_ADDR'], success=True)

        log_event(user, EventLog.EventTypes.LOGIN, request=request)

        return {"user": user}


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    captcha = serializers.CharField(write_only=True)

    def validate(self, data):
        # old_password = decryption(data['old_password'])
        # new_password = decryption(data['new_password'])
        request = self.context.get("request")
        captcha_key = get_anonymous_cache_key(request)
        cached_captcha = cache.get(captcha_key)

        if not cached_captcha:
            raise serializers.ValidationError("کپچا منقضی شده است، لطفاً دوباره دریافت کنید.")

        if data["captcha"] != cached_captcha:
            raise serializers.ValidationError("کپچا اشتباه است.")

        cache.delete(captcha_key)

        if IllPassword.objects.filter(password=data["new_password"]).exists():
            raise serializers.ValidationError("رمز عبور غیرمجاز است")

        if not request.user.check_password(data['old_password']):
            raise serializers.ValidationError("رمز عبور فعلی اشتباه است.")

        return data

    def validate_new_password(self, value):
        # value = decryption(value)
        validate_password(value)
        return value


class AdminChangePasswordSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    new_password = serializers.CharField(write_only=True)
    captcha = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        request = self.context.get("request")
        # captcha_key = get_anonymous_cache_key(request)
        # cached_captcha = cache.get(captcha_key)
        #
        # if not cached_captcha:
        #     raise serializers.ValidationError( "کپچا منقضی شده است، لطفاً دوباره دریافت کنید.")
        #
        # if data["captcha"] != cached_captcha:
        #     raise serializers.ValidationError("کپچا اشتباه است.")
        # cache.delete(captcha_key)

        # new_password = decryption(data['new_password'])
        if IllPassword.objects.filter(password=data["new_password"]).exists():
            raise serializers.ValidationError("رمز عبور غیرمجاز است")
        user = User.objects.filter(id=data['user_id']).first()
        data['user'] = user
        if not user:
            raise serializers.ValidationError("کاربری با این شناسه یافت نشد.")
        return data

    def save(self, **kwargs):
        # new_password = decryption(self.validated_data['new_password'])
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.force_password_change = True
        user.save()
        return user


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'codename')


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True)

    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'permissions')


class RoleCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'permissions')


class GroupSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True)
    organization = serializers.SerializerMethodField()

    class Meta:
        model = UserGroup
        fields = ('id', 'name', 'description', 'roles', 'organization')

    def get_organization(self, obj):
        return obj.organization.name if obj.organization else None


class GroupCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = ('id', 'name', 'description', 'roles', 'organization')


class UserGetSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True)
    organization = serializers.SerializerMethodField()

    class Meta:
        model = User
        # fields = ('id', 'username', 'last_login', 'is_active', 'groups')
        fields = ['id', 'username', 'first_name', 'last_name', 'phone_number', 'national_number', 'organization', 'groups']

    def get_organization(self, obj):
        return obj.organization.name if obj.organization else None


class USerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = ('username', 'groups', 'is_active')
        fields = ['id', 'username', 'first_name', 'last_name', 'phone_number', 'national_number', 'organization', 'groups']


class LoginAttemptsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginAttempt
        fields = ('id', 'username', 'ip_address', 'success', 'create')


class IllUsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = IllUsername
        fields = ('id', 'username')


class IllPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = IllPassword
        fields = ('id', 'password')















from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from core.utils import get_anonymous_cache_key


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(validators=[])

    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('کاربر با این نام کاربری وجود دارد')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    captcha = serializers.CharField(write_only=True)

    def validate(self, data):
        request = self.context.get("request")
        captcha_key = get_anonymous_cache_key(request)
        cached_captcha = cache.get(captcha_key)

        if not cached_captcha:
            raise serializers.ValidationError("کپچا منقضی شده است، لطفاً دوباره دریافت کنید.")

        if data["captcha"] != cached_captcha:
            raise serializers.ValidationError("کپچا اشتباه است.")

        cache.delete(captcha_key)

        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("نام کاربری یا رمز عبور اشتباه است.")

        return {"user": user}

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    captcha = serializers.CharField(write_only=True)

    def validate(self, data):
        request = self.context.get("request")
        captcha_key = get_anonymous_cache_key(request)
        cached_captcha = cache.get(captcha_key)

        if not cached_captcha:
            raise serializers.ValidationError("کپچا منقضی شده است، لطفاً دوباره دریافت کنید.")

        if data["captcha"] != cached_captcha:
            raise serializers.ValidationError("کپچا اشتباه است.")

        cache.delete(captcha_key)

        if not request.user.check_password(data['old_password']):
            raise serializers.ValidationError("رمز عبور فعلی اشتباه است.")

        return data

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def save(self, **kwargs):
        """ تغییر رمز عبور و ذخیره در پایگاه داده """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

class AdminChangePasswordSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    new_password = serializers.CharField(write_only=True)
    captcha = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        request = self.context.get("request")
        captcha_key = get_anonymous_cache_key(request)
        cached_captcha = cache.get(captcha_key)

        if not cached_captcha:
            raise serializers.ValidationError( "کپچا منقضی شده است، لطفاً دوباره دریافت کنید.")

        if data["captcha"] != cached_captcha:
            raise serializers.ValidationError("کپچا اشتباه است.")
        cache.delete(captcha_key)
        user = User.objects.filter(id=data['user_id']).first()
        data['user'] = user
        if not user:
            raise serializers.ValidationError("کاربری با این شناسه یافت نشد.")
        return data

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
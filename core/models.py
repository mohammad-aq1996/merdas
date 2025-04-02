import django_jalali.db.models as jmodels
from django.db import models


class BaseModel(models.Model):
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Settings(BaseModel):
    config = models.JSONField(default=dict)

    @classmethod
    def get_setting(cls, key, default=None):
        """دریافت مقدار یک تنظیم خاص، در صورت نبود مقدار پیش‌فرض برمی‌گرداند"""
        settings, created = cls.objects.get_or_create(id=1)
        return settings.config.get(key, default)

    @classmethod
    def set_setting(cls, key, value):
        """تنظیم مقدار یک کلید در تنظیمات"""
        settings, created = cls.objects.get_or_create(id=1)
        settings.config[key] = value
        settings.save()

    @classmethod
    def get_all_settings(cls):
        """دریافت تمامی تنظیمات ذخیره شده"""
        settings, created = cls.objects.get_or_create(id=1)
        return settings.config
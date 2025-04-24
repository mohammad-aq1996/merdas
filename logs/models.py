from django.db import models
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from core.models import BaseModel


User = get_user_model()

class EventLog(BaseModel):
    class EventTypes(models.TextChoices):
        LOGIN = "LOGIN", "ورود به سامانه"
        LOGOUT = "LOGOUT", "خروج از سامانه"
        CREATE_USER = "CREATE_USER", "ایجاد کاربر"
        UPDATE_USER = "UPDATE_USER", "ویرایش کاربر"
        DELETE_USER = "DELETE_USER", "حذف کاربر"
        CREATE_ROLE = "CREATE_ROLE", "ایجاد نقش"
        UPDATE_ROLE = "UPDATE_ROLE", "ویرایش نقش"
        DELETE_ROLE = "DELETE_ROLE", "حذف نقش"
        CREATE_GROUP = "CREATE_GROUP", "ایجاد گروه"
        UPDATE_GROUP = "UPDATE_GROUP", "ویرایش گروه"
        DELETE_GROUP = "DELETE_GROUP", "حذف گروه"
        USER_LOCKED = "USER_LOCKED", "لاک شدن کاربر"
        USER_UNLOCKED = "USER_UNLOCKED", "آنلاک شدن کاربر"
        PERMISSION_DENIED = "PERMISSION_DENIED", "دسترسی غیرمجاز"

    event_type = models.CharField(max_length=50, choices=EventTypes.choices)  # نوع رویداد
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # کاربر ایجادکننده رویداد
    success = models.BooleanField(default=True)  # موفقیت یا شکست رویداد
    timestamp = models.DateTimeField(default=now)  # زمان رویداد
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # آدرس IP
    user_agent = models.TextField(blank=True, null=True)  # مرورگر یا کلاینت
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.user} - {self.timestamp}"

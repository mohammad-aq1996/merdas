from django.db import models
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from core.models import BaseModel


User = get_user_model()

class EventLog(BaseModel):
    EVENT_TYPES = [
        ("LOGIN", "ورود به سامانه"),
        ("LOGOUT", "خروج از سامانه"),
        ("CREATE_USER", "ایجاد کاربر"),
        ("UPDATE_USER", "ویرایش کاربر"),
        ("DELETE_USER", "حذف کاربر"),
        ("CREATE_ROLE", "ایجاد نقش"),
        ("UPDATE_ROLE", "ویرایش نقش"),
        ("DELETE_ROLE", "حذف نقش"),
        ("CREATE_GROUP", "ایجاد گروه"),
        ("UPDATE_GROUP", "ویرایش گروه"),
        ("DELETE_GROUP", "حذف گروه"),
        ("USER_LOCKED", "لاک شدن کاربر"),
        ("USER_UNLOCKED", "آنلاک شدن کاربر"),
        ("UNAUTHORIZED_ACCESS", "تلاش برای دسترسی غیرمجاز"),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)  # نوع رویداد
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # کاربر ایجادکننده رویداد
    success = models.BooleanField(default=True)  # موفقیت یا شکست رویداد
    timestamp = models.DateTimeField(default=now)  # زمان رویداد
    metadata = models.JSONField(default=dict, blank=True)  # اطلاعات اضافی (مثل IP کاربر، مسیر API و ...)

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.user} - {self.timestamp}"

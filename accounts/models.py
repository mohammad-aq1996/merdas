from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import AbstractUser, Permission
from django.utils.timezone import now, timedelta
from core.models import BaseModel
from django.contrib.auth.hashers import make_password, check_password


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(Permission, related_name="roles", blank=True)

    def __str__(self):
        return self.name

class UserGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    roles = models.ManyToManyField(Role, related_name="groups", blank=True)


class UserManager(BaseUserManager):
    def create_user(self, username, password=None):
        if not username:
            raise ValueError('Username is required')

        user = self.model(username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        user = self.create_user(username, password)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    force_password_change = models.BooleanField(default=True)
    password_changed_at = models.DateTimeField(auto_now_add=True)  # زمان آخرین تغییر پسورد

    old_passwords = models.JSONField(default=list)

    groups = models.ManyToManyField(UserGroup, related_name="users", blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

    def password_expired(self):
        return now() - self.password_changed_at > timedelta(days=30)

    def must_change_password(self):
        """ چک می‌کند که آیا کاربر باید پسوردش را تغییر دهد یا نه """
        return self.password_expired() or self.force_password_change

    def check_old_passwords(self, new_password):
        """ بررسی می‌کند که آیا پسورد جدید در لیست پسوردهای قدیمی هست یا نه """
        return any(check_password(new_password, old_pwd) for old_pwd in self.old_passwords)

    def update_password(self, new_password, max_old_passwords=5):
        """ ذخیره پسورد جدید و حذف قدیمی‌ها از لیست """
        if self.check_old_passwords(new_password):
            raise ValueError(f"استفاده از {max_old_passwords} رمزعبور قبلی مجاز نمیباشد")

        hashed_password = make_password(new_password)

        # اضافه کردن هش جدید به لیست و محدود کردن به `max_old_passwords`
        self.old_passwords.insert(0, hashed_password)
        self.old_passwords = self.old_passwords[:max_old_passwords]

        self.password = hashed_password
        self.password_changed_at = now()
        self.force_password_change = False  # اجبار تغییر پسورد برداشته می‌شود
        self.save()

class LoginAttempt(BaseModel):
    create = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} - {self.success}"

    class Meta:
        ordering = ['-created_at']


class IllUsername(BaseModel):
    username = models.CharField(max_length=255)


class IllPassword(BaseModel):
    password = models.CharField(max_length=255)
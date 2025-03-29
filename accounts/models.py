from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import AbstractUser, Permission
from django.utils.timezone import now, timedelta
from core.models import BaseModel


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

    groups = models.ManyToManyField(UserGroup, related_name="users", blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

    def password_expired(self):
        return now() - self.password_changed_at > timedelta(days=90)

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
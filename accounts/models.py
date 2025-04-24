from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import AbstractUser, Permission
from django.utils.timezone import now, timedelta
from core.models import BaseModel, Settings
from django.contrib.auth.hashers import make_password, check_password
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth.models import Group


class Role(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(Permission, related_name="roles", blank=True)

    def __str__(self):
        return self.name


class UserGroup(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    organization = models.ForeignKey("Organization", on_delete=models.PROTECT, related_name="groups")
    roles = models.ManyToManyField(Role, related_name="groups")


class UserManager(BaseUserManager):
    def create_user(self, username, first_name, last_name, national_number, organization, group, phone_number=None, password=None):
        if not username:
            raise ValueError('نام کاربری ضرور است')
        if not first_name:
            raise ValueError('نام ضرور است')
        if not last_name:
            raise ValueError('نام خانوادگی ضرور است')
        if not national_number:
            raise ValueError('کد ملی ضرور است')
        if not organization:
            raise ValueError('سازمان ضرور است')
        if not group:
            raise ValueError('گروه ضرور است')

        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name,
            national_number=national_number,
            organization=organization,
            group=group,
            phone_number=phone_number
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        user = self.model(
            username=username,
        )
        user.set_password(password)

        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(BaseModel, AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)  # نیاز به مدیریت دستی داریم
    is_admin_blocked = models.BooleanField(default=False)

    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    national_number = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=255, blank=True, null=True)
    organization = models.ForeignKey("Organization", on_delete=models.PROTECT, blank=True, null=True)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, blank=True, null=True, related_name="users")

    force_password_change = models.BooleanField(default=True)
    password_changed_at = models.DateTimeField(auto_now_add=True)  # زمان آخرین تغییر پسورد

    old_passwords = models.JSONField(default=list, blank=True, null=True)

    # groups = models.ManyToManyField(UserGroup, related_name="users", blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_all_permissions(self):
        if self.is_superuser:
            return set(Permission.objects.values_list("codename", flat=True))  # همه پرمیژن‌ها
        roles = Role.objects.filter(groups__users=self)

        permissions = Permission.objects.filter(roles__in=roles).values_list(
            "content_type__app_label", "codename"
        )
        return {f"{app}.{code}" for app, code in permissions}

    def has_perm(self, perm):
        if self.is_superuser:
            return True
        return perm in self.get_all_permissions()

    def has_module_perms(self, app_label):
        if self.is_superuser:
            return True
        return any(perm.startswith(f"{app_label}.") for perm in self.get_all_permissions())

    def password_expired(self):
        expire_days = int(Settings.get_setting("PASSWORD_EXPIRATION_DAYS", default=15))
        return now() - self.password_changed_at > timedelta(days=expire_days)

    def must_change_password(self):
        """ چک می‌کند که آیا کاربر باید پسوردش را تغییر دهد یا نه """
        return self.password_expired() or self.force_password_change

    def check_old_passwords(self, new_password):
        """ بررسی می‌کند که آیا پسورد جدید در لیست پسوردهای قدیمی هست یا نه """
        return any(check_password(new_password, old_pwd) for old_pwd in self.old_passwords)

    def update_password(self, new_password):
        max_old_passwords = int(Settings.get_setting("PASSWORD_HISTORY_LIMIT", default=5))
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


class OrganizationType(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Organization(BaseModel, MPTTModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    organization_type = models.ForeignKey(OrganizationType, on_delete=models.CASCADE)

    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    class MPTTMeta:
        order_insertion_by = ["name"]

    def __str__(self):
        return self.name
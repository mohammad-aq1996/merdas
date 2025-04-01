from rest_framework.permissions import BasePermission

class GroupPermissions(BasePermission):
    """
    چک می‌کنه که آیا کاربر پرمیژن موردنیاز رو از طریق گروه‌ها داره.
    """
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_superuser:
            return True
        if not request.user.is_authenticated:  # بررسی لاگین بودن
            return False

        # چک کردن پرمیژن بر اساس متد HTTP
        perms_map = {
            "GET": "view",
            "OPTIONS": "view",
            "HEAD": "view",
            "POST": "add",
            "PUT": "change",
            "PATCH": "change",
            "DELETE": "delete",
        }

        # **اینجا خودمون اسم مدل رو از queryset استخراج می‌کنیم**
        if hasattr(view, "queryset") and view.queryset is not None:
            model_name = view.queryset.model._meta.model_name
            app_label = view.queryset.model._meta.app_label
        else:
            return False  # اگه مدل مشخص نیست، پرمیژن رو رد کن

        # ساختن نام پرمیژن جنگو (مثلاً "auth.view_user")
        required_permission = f"{app_label}.{perms_map[request.method]}_{model_name}"
        return request.user.has_perm(required_permission)

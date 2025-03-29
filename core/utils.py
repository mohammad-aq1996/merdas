from rest_framework.response import Response
from django.utils.timezone import now


class CustomResponse:
    @staticmethod
    def success(message, data=None, status=200):
        response = {
            "success": True,
            "message": message,
            "data": data
        }
        return Response(response, status=status)

    @staticmethod
    def error(message, errors=None, status=400):
        response = {
            "success": False,
            "message": message,
            "errors": errors
        }
        return Response(response, status=status)


def get_anonymous_cache_key(request, prefix='anon_cache'):
    ip = request.META.get('REMOTE_ADDR', '')  # Or use the IP detection method from earlier
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:20]  # Truncate to prevent long keys
    key = f"{prefix}:{ip}:{user_agent}"
    return key


# def set_new_password(user, new_password):
#     user.set_password(new_password)  # تغییر پسورد
#     user.password_changed_at = now()  # ثبت زمان جدید
#     user.force_password_change = False  # اگر مجبور به تغییر پسورد بوده، ریست بشه
#     user.save()
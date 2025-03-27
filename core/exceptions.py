from .utils import CustomResponse
from rest_framework.views import exception_handler
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, NotFound, ValidationError


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        return CustomResponse.error("داده‌های ورودی معتبر نیستند", errors=exc.detail, status=400)

    if isinstance(exc, NotAuthenticated):
        return CustomResponse.error("برای دسترسی باید وارد شوید", status=401)

    if isinstance(exc, PermissionDenied):
        return CustomResponse.error("دسترسی ندارید", status=403)

    if isinstance(exc, NotFound):
        return CustomResponse.error("موردی یافت نشد", status=404)

    if response is not None:
        return CustomResponse.error("مشکلی در پردازش درخواست وجود دارد",
                                    errors=response.data,
                                    status=response.status_code)

    return CustomResponse.error("خطای داخلی سرور", status=500)

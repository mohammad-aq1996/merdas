from .models import EventLog

def log_event(user, event_type, success=True, request=None, description=None):
    """
    ثبت رویداد در دیتابیس
    :param user: کاربری که رویداد را ایجاد کرده
    :param event_type: نوع رویداد (از EventLog.EventTypes)
    :param success: آیا عملیات موفق بوده یا نه
    :param request: شیء request برای گرفتن IP و User-Agent
    :param description: اطلاعات اضافی در قالب دیکشنری
    """
    if description is None:
        description = {}

    ip_address = None
    user_agent = None

    if request:
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")

    EventLog.objects.create(
        user=user,
        event_type=event_type,
        success=success,
        ip_address=ip_address,
        user_agent=user_agent,
        description=description
    )

def get_client_ip(request):
    """ گرفتن IP واقعی کاربر """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip

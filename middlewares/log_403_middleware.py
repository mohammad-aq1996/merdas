# middlewares/log_403_middleware.py
from django.utils.deprecation import MiddlewareMixin
from logs.utils import log_event
from logs.models import EventLog


class Log403Middleware(MiddlewareMixin):
    def process_response(self, request, response):
        if response.status_code == 403:
            log_event(
                user=request.user if request.user.is_authenticated else None,
                event_type=EventLog.EventTypes.PERMISSION_DENIED,
                success=False,
                request=request,
                description={
                    "message": "دسترسی غیرمجاز (403)",
                    "path": request.path,
                    "method": request.method,
                }
            )
        return response

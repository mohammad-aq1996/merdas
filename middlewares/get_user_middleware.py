import threading

_request_local = threading.local()

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_local.request = request
        response = self.get_response(request)
        return response

def get_current_user():
    """ گرفتن یوزر لاگین‌شده همراه با `request` """
    request = getattr(_request_local, "request", None)
    if request and hasattr(request, "user"):
        user = request.user
        user.request = request  # 📌 ذخیره `request` داخل یوزر
        return user
    return None

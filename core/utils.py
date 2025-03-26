def get_anonymous_cache_key(request, prefix='anon_cache'):
    ip = request.META.get('REMOTE_ADDR', '')  # Or use the IP detection method from earlier
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:20]  # Truncate to prevent long keys
    key = f"{prefix}:{ip}:{user_agent}"
    return key
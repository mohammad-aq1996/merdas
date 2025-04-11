from auditlog.registry import auditlog
from .models import Role, UserGroup, User, LoginAttempt, IllUsername, IllPassword

def register_auditlog_models():
    auditlog.register(User)
    auditlog.register(Role)
    auditlog.register(UserGroup)
    auditlog.register(LoginAttempt)
    auditlog.register(IllUsername)
    auditlog.register(IllPassword)
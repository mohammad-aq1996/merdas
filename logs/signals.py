from django.dispatch import receiver
from .models import EventLog
from .utils import log_event
from accounts.models import User, UserGroup, Role
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete
from logs.middleware import get_current_user


User = get_user_model()


@receiver(post_save, sender=User)
def log_user_create_or_update(sender, instance, created, **kwargs):
    actor = get_current_user()  # 📌 گرفتن یوزری که درخواست داده
    request = getattr(actor, "request", None)  # 📌 گرفتن `request`

    if created:
        event_type = EventLog.EventTypes.CREATE_USER
    else:
        event_type = EventLog.EventTypes.UPDATE_USER

    log_event(actor, event_type, request=request)

@receiver(post_delete, sender=User)
def log_user_delete(sender, instance, **kwargs):
    actor = get_current_user()  # 📌 گرفتن یوزری که درخواست داده

    log_event(actor, EventLog.EventTypes.DELETE_USER)

@receiver(post_save, sender=UserGroup)
def log_group_create_or_update(sender, instance, created, **kwargs):
    actor = get_current_user()
    request = getattr(actor, "request", None)

    if created:
        event_type = EventLog.EventTypes.CREATE_GROUP
    else:
        event_type = EventLog.EventTypes.UPDATE_GROUP

    log_event(actor, event_type, request=request)

@receiver(post_delete, sender=User)
def log_group_delete(sender, instance, **kwargs):
    actor = get_current_user()

    log_event(actor, EventLog.EventTypes.DELETE_GROUP)

@receiver(post_save, sender=UserGroup)
def log_role_create_or_update(sender, instance, created, **kwargs):
    actor = get_current_user()
    request = getattr(actor, "request", None)

    if created:
        event_type = EventLog.EventTypes.DELETE_ROLE
    else:
        event_type = EventLog.EventTypes.DELETE_ROLE

    log_event(actor, event_type, request=request)

@receiver(post_delete, sender=User)
def log_role_delete(sender, instance, **kwargs):
    actor = get_current_user()

    log_event(actor, EventLog.EventTypes.DELETE_ROLE)
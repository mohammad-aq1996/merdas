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
    try:
        actor = get_current_user()  # 📌 گرفتن یوزری که درخواست داده
        request = getattr(actor, "request", None)  # 📌 گرفتن `request`
    except AttributeError:
        actor = None
        request = None

    if created:
        event_type = EventLog.EventTypes.CREATE_USER
        description = f"user: {instance.username} created by {actor.username if actor else None}"
    else:
        event_type = EventLog.EventTypes.UPDATE_USER
        description = f"user: {instance.username} updated by {actor.username if actor else None}"

    log_event(actor, event_type, request=request, description=description)

@receiver(post_delete, sender=User)
def log_user_delete(sender, instance, **kwargs):
    actor = get_current_user()  # 📌 گرفتن یوزری که درخواست داده
    description = f"user: {instance.username} deleted by {actor.username}"

    log_event(actor, EventLog.EventTypes.DELETE_USER, description=description)

@receiver(post_save, sender=UserGroup)
def log_group_create_or_update(sender, instance, created, **kwargs):
    actor = get_current_user()
    request = getattr(actor, "request", None)

    if created:
        event_type = EventLog.EventTypes.CREATE_GROUP
        description = f"group {instance.name} created by {actor.username}"
    else:
        event_type = EventLog.EventTypes.UPDATE_GROUP
        description = f"group {instance.name} updated by {actor.username}"

    log_event(actor, event_type, request=request, description=description)

@receiver(post_delete, sender=UserGroup)
def log_group_delete(sender, instance, **kwargs):
    actor = get_current_user()
    description = f"group: {instance.name} deleted by {actor.username}"

    log_event(actor, EventLog.EventTypes.DELETE_GROUP, description=description)

@receiver(post_save, sender=Role)
def log_role_create_or_update(sender, instance, created, **kwargs):
    actor = get_current_user()
    request = getattr(actor, "request", None)

    if created:
        event_type = EventLog.EventTypes.DELETE_ROLE
        description = f"{instance.name} created by {actor.username}"
    else:
        event_type = EventLog.EventTypes.DELETE_ROLE
        description = f"role: {instance.name} updated by {actor.username}"

    log_event(actor, event_type, request=request, description=description)

@receiver(post_delete, sender=Role)
def log_role_delete(sender, instance, **kwargs):
    actor = get_current_user()
    description = f"role: {instance.name} deleted by {actor.username}"

    log_event(actor, EventLog.EventTypes.DELETE_ROLE, description=description)
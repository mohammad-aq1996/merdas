from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserGroup


@receiver(post_save, sender=User)
def assign_group_based_on_organization(sender, instance, **kwargs):
    if instance.organization:
        group = UserGroup.objects.filter(organization=instance.organization).first()
        if group:
            instance.groups.set([group])

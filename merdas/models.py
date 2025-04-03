from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.core.exceptions import ValidationError
from core.models import BaseModel


class OrganizationType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Organization(MPTTModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    organization_type = models.ForeignKey(OrganizationType, on_delete=models.CASCADE)

    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    class MPTTMeta:
        order_insertion_by = ["name"]

    def __str__(self):
        return self.name


class SR(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class FR(BaseModel):
    title = models.CharField(max_length=255)
    weight = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    sr = models.ManyToManyField(SR, related_name="fr")

    def __str__(self):
        return self.title


class Standard(BaseModel):
    title = models.CharField(max_length=255)
    fr = models.ManyToManyField(FR, related_name='standards')

    def __str__(self):
        return self.title

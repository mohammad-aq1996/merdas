import django_jalali.db.models as jmodels
from django.db import models


class BaseModel(models.Model):
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)

    class Meta:
        abstract = True


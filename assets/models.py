from django.db import models
from django.contrib.postgres.fields import ArrayField
import django_jalali.db.models as jmodels

from accounts.models import User
from core.models import BaseModel


# ---------- Attribute Dictionary ----------

class AttributeCategory(BaseModel):
    title_en = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.title

def _empty_list():
    return []

class Attribute(BaseModel):
    class PropertyType(models.TextChoices):
        INT   = 'int',   'Integer'
        FLOAT = 'float', 'Float'
        STR   = 'str',   'String'
        BOOL  = 'bool',  'Boolean'
        DATE  = 'date',  'Date'
        CHOICE= 'choice','Choice'

    title = models.CharField(max_length=200)
    title_en = models.CharField(max_length=200)
    property_type = models.CharField(max_length=10, choices=PropertyType.choices)
    category = models.ForeignKey(AttributeCategory, null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="attributes")

    choices = ArrayField(
        base_field=models.CharField(max_length=150),
        default=_empty_list,  # همیشه از callable استفاده کن
        blank=True,
        help_text="لیست برچسب‌ها"
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.title


# ---------- Assets & Type Rules ----------

class Asset(BaseModel):
    class AssetType(models.TextChoices):
        IT = 'it', 'دارایی‌های IT'
        NON_IT = 'non_it', 'دارایی‌های غیر IT'

    asset_type = models.CharField(max_length=32, choices=AssetType.choices)
    title = models.CharField(max_length=250)
    code = models.CharField(max_length=120, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_registered = models.BooleanField(default=True, db_index=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['asset_type']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return f"[{self.asset_type}] {self.title}"


class AssetUnit(BaseModel):
    """
    هر ردیف = یک «نمونه» از Asset (مثلاً یکی از پرینترها)
    """
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE, related_name='units')
    label = models.CharField(max_length=120, null=True, blank=True, db_index=True)  # مثل "PRN-1" یا "HP-001"
    code  = models.CharField(max_length=120, null=True, blank=True, unique=True)    # اگر code نمی‌دهی، خالی بگذار
    is_active = models.BooleanField(default=True)
    is_registered = models.BooleanField(default=True, db_index=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['asset']),
            models.Index(fields=['label']),
        ]

    def __str__(self): return f"{self.asset.title} / {self.label or self.code or self.id}"


class AssetTypeAttribute(BaseModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="type_rules")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="type_rules")
    is_required = models.BooleanField(default=False)
    is_multi = models.BooleanField(default=False)
    min_count = models.PositiveIntegerField(default=0)
    max_count = models.PositiveIntegerField(null=True, blank=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.asset.title} :: (req={self.is_required}, multi={self.is_multi})"


# ---------- EAV Values ----------

class AssetAttributeValue(BaseModel):
    class Status(models.TextChoices):
        REGISTERED = 'registered', 'رجیستر شده'
        UNREGISTERED = 'unregistered', 'رجیستر نشده'

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="values")
    unit  = models.ForeignKey('AssetUnit', on_delete=models.CASCADE, null=True, blank=True, related_name='values')

    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="values")

    # ستون‌های نوع‌دار — فقط یکی باید پر باشد (با CheckConstraint سطح DB)
    value_int = models.BigIntegerField(null=True, blank=True)
    value_float = models.FloatField(null=True, blank=True)
    value_str = models.TextField(null=True, blank=True)
    value_bool = models.BooleanField(null=True, blank=True)
    value_date = models.DateField(null=True, blank=True)
    choice = models.TextField(null=True, blank=True)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.REGISTERED)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['asset', 'attribute'], name='idx_v_asset_attr'),
            models.Index(fields=['status']),
            # اگر روی تاریخ یا عدد زیاد فیلتر می‌کنی، ایندکس‌های زیر رو نگه دار:
            models.Index(fields=['value_date'], name='idx_v_date'),
            models.Index(fields=['value_int'], name='idx_v_int'),
            models.Index(fields=['value_float'], name='idx_v_float'),
        ]

    def __str__(self):
        return self.asset.title


# ---------- Relations (Temporal Edges) ----------

class Relation(BaseModel):
    key = models.CharField(max_length=100, unique=True)  # مثل: depends_on / connected_to / owns
    name = models.CharField(max_length=200)              # برچسب خوانا

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.key


class AssetRelation(BaseModel):
    relation = models.ForeignKey(Relation, on_delete=models.RESTRICT, related_name="edges")
    source_asset = models.ForeignKey(AssetUnit, on_delete=models.CASCADE, related_name="out_edges")
    target_asset = models.ForeignKey(AssetUnit, on_delete=models.CASCADE, related_name="in_edges")

    start_date = jmodels.jDateField(null=True, blank=True)
    end_date =  jmodels.jDateField(null=True, blank=True)

    attribute_value = models.ForeignKey(AssetAttributeValue, on_delete=models.SET_NULL, related_name="edges", null=True)

    note = models.TextField(null=True, blank=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.relation.key}: {self.source_asset_id} -> {self.target_asset_id}"

# ---------- Upload CSB ------------------


class ImportSession(BaseModel):
    class State(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        MAPPED   = "mapped",   "Mapped"
        EDITED   = "edited",   "Edited"
        COMMITTED= "committed","Committed"

    file = models.FileField(upload_to="imports/%Y/%m/%d/")
    filename = models.CharField(max_length=255)
    has_header = models.BooleanField(default=True)
    delimiter = models.CharField(max_length=4, default=",")
    total_rows = models.PositiveIntegerField(default=0)
    headers = models.JSONField(default=list)        # ["col1","col2",...]
    preview_rows = models.JSONField(default=list)   # [ {...}, ... ] 10 ردیف اول به شکل dict

    # mapping
    asset_column = models.CharField(max_length=255, null=True, blank=True)
    asset_lookup_field = models.CharField(          # "id" | "code" | "title"
        max_length=20, default="title"
    )
    attribute_map = models.JSONField(default=dict)  # {"col_name": "attribute_uuid", ...}

    state = models.CharField(max_length=16, choices=State.choices, default=State.UPLOADED)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)


class ImportIssue(BaseModel):
    class Level(models.TextChoices):
        ERROR = "error", "Error"
        WARN  = "warn", "Warn"

    session = models.ForeignKey(ImportSession, on_delete=models.CASCADE, related_name="issues")
    row_index = models.PositiveIntegerField()  # 1-based index (بدون هدر)
    asset_ref = models.CharField(max_length=255, blank=True, null=True)  # مقدار ستون asset در CSV
    asset = models.ForeignKey(Asset, null=True, blank=True, on_delete=models.SET_NULL)

    attribute = models.ForeignKey(Attribute, null=True, blank=True, on_delete=models.SET_NULL)
    level = models.CharField(max_length=8, choices=Level.choices, default=Level.ERROR)
    code = models.CharField(max_length=64)   # e.g., "REQUIRED_MISSING", "TYPE_INVALID", "CHOICE_NOT_FOUND", "MIN_MAX"
    message = models.TextField()






















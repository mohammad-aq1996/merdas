from django.db import models

from accounts.models import User
from core.models import BaseModel


# ---------- Attribute Dictionary ----------

class AttributeCategory(BaseModel):
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=200)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.key} - {self.value}"


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

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.title


class AttributeChoice(BaseModel):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="choices")
    value = models.CharField(max_length=200)  # مقدار ذخیره‌ای
    label = models.CharField(max_length=200, null=True, blank=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = "attribute_choice"
        constraints = [
            models.UniqueConstraint(fields=['attribute', 'value'], name='uq_attrchoice_attr_value')
        ]

    def __str__(self):
        return self.value

# ---------- Assets & Type Rules ----------

class Asset(BaseModel):
    class AssetType(models.TextChoices):
        IT = 'it', 'دارایی‌های IT'
        NON_IT = 'non_it', 'دارایی‌های غیر IT'

    asset_type = models.CharField(max_length=32, choices=AssetType.choices)
    title = models.CharField(max_length=250)
    code = models.CharField(max_length=120, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['asset_type']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return f"[{self.asset_type}] {self.title}"


class AssetTypeAttribute(BaseModel):
    asset_type = models.CharField(max_length=32, choices=Asset.AssetType.choices)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="type_rules")
    is_required = models.BooleanField(default=False)
    is_multi = models.BooleanField(default=False)
    min_count = models.PositiveIntegerField(default=0)
    max_count = models.PositiveIntegerField(null=True, blank=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['asset_type', 'attribute'], name='uq_type_attribute')
        ]

    def __str__(self):
        return f"{self.asset_type} :: (req={self.is_required}, multi={self.is_multi})"


# ---------- EAV Values ----------

class AssetAttributeValue(BaseModel):
    class Status(models.TextChoices):
        REGISTERED = 'registered', 'رجیستر شده'
        UNREGISTERED = 'unregistered', 'رجیستر نشده'

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="values")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="values")

    # ستون‌های نوع‌دار — فقط یکی باید پر باشد (با CheckConstraint سطح DB)
    value_int = models.BigIntegerField(null=True, blank=True)
    value_float = models.FloatField(null=True, blank=True)
    value_str = models.TextField(null=True, blank=True)
    value_bool = models.BooleanField(null=True, blank=True)
    value_date = models.DateField(null=True, blank=True)
    choice = models.ForeignKey(AttributeChoice, null=True, blank=True,
                               on_delete=models.RESTRICT, related_name="used_in_values")

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
    source_asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="out_edges")
    target_asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="in_edges")

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    attribute_value = models.ForeignKey(AssetAttributeValue, on_delete=models.SET_NULL, related_name="edges", null=True)

    note = models.TextField(null=True, blank=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.relation.key}: {self.source_asset_id} -> {self.target_asset_id}"


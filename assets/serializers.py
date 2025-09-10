from rest_framework import serializers
from assets.models import *
from django.db import transaction
from datetime import datetime, date


class AttributeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeCategory
        fields = ('id',
                  'created_at',
                  'updated_at',
                  'title_en',
                  'title')


class AttributeSerializer(serializers.ModelSerializer):
    category_value = serializers.CharField(source='category.title', read_only=True)
    choices = serializers.ListField(
        child=serializers.CharField(max_length=150),
        allow_empty=True,
        required=False
    )

    class Meta:
        model = Attribute
        fields = ('id',
                  'created_at',
                  'updated_at',
                  'title',
                  'title_en',
                  'property_type',
                  'category',
                  'category_value',
                  'choices')

    def validate_choices(self, value):
        cleaned = [v.strip() for v in value if v.strip()]

        if len(cleaned) != len(set(cleaned)):
            raise serializers.ValidationError("مقادیر تکراری مجاز نیست.")
        return cleaned


class AssetTypeAttributeSerializer(serializers.ModelSerializer):
    attribute_read = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AssetTypeAttribute
        fields = ('attribute',
                  'is_required',
                  'is_multi',
                  'attribute_read',)

    def get_attribute_read(self, obj):
        return AttributeSerializer(obj.attribute).data


class AssetTypeAttributeWriteSerializer(serializers.ModelSerializer):
    attribute = serializers.PrimaryKeyRelatedField(queryset=Attribute.objects.all())

    class Meta:
        model = AssetTypeAttribute
        fields = ("attribute", "is_required", "is_multi", "min_count", "max_count")

    def validate(self, attrs):
        is_multi = attrs.get("is_multi", False)
        min_count = attrs.get("min_count", 0) or 0
        max_count = attrs.get("max_count", None)

        # min/max منطقی
        if min_count < 0:
            raise serializers.ValidationError({"min_count": "نمی‌تواند منفی باشد."})
        if max_count is not None and max_count < 1:
            raise serializers.ValidationError({"max_count": "اگر تعیین شود باید ≥ 1 باشد."})
        if max_count is not None and min_count > max_count:
            raise serializers.ValidationError({"max_count": "باید ≥ min_count باشد."})

        # اگر تک‌مقداری، min/max را محدود کن
        if not is_multi:
            if min_count > 1:
                raise serializers.ValidationError({"min_count": "برای فیلد تک‌مقداری باید ≤ 1 باشد."})
            if max_count is not None and max_count > 1:
                raise serializers.ValidationError({"max_count": "برای فیلد تک‌مقداری باید ≤ 1 باشد."})

        return attrs


class AssetCreateUpdateSerializer(serializers.ModelSerializer):
    attributes = AssetTypeAttributeWriteSerializer(many=True, required=False)

    class Meta:
        model = Asset
        fields = ("title", "asset_type", "code", "attributes")

    def _validate_unique_attributes(self, attrs_list):
        attr_ids = [str(item["attribute"].pk) for item in attrs_list]
        if len(attr_ids) != len(set(attr_ids)):
            raise serializers.ValidationError({"attributes": "خصیصه‌های تکراری مجاز نیست."})

    def create(self, validated_data):
        attrs_list = validated_data.pop("attributes", [])
        owner = validated_data.pop("owner", None)  # از serializer.save(owner=request.user) می‌آد

        if attrs_list:
            self._validate_unique_attributes(attrs_list)

        with transaction.atomic():
            asset = Asset.objects.create(owner=owner, **validated_data)

            rules = [
                AssetTypeAttribute(
                    asset=asset,
                    attribute=item["attribute"],
                    is_required=item.get("is_required", False),
                    is_multi=item.get("is_multi", False),
                    min_count=item.get("min_count", 0) or 0,
                    max_count=item.get("max_count"),
                    owner=owner,
                )
                for item in attrs_list
            ]
            if rules:
                AssetTypeAttribute.objects.bulk_create(rules, ignore_conflicts=False)

        return asset

    @transaction.atomic
    def update(self, instance, validated_data):
        attrs_list = validated_data.pop("attributes", None)  # اگر نیاد، دست نزن
        owner = validated_data.pop("owner", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)

        instance.save()

        if attrs_list is not None:
            self._validate_unique_attributes(attrs_list)
            instance.type_rules.all().delete()
            rules = [
                AssetTypeAttribute(
                    asset=instance,
                    attribute=item["attribute"],
                    is_required=item.get("is_required", False),
                    is_multi=item.get("is_multi", False),
                    min_count=item.get("min_count", 0) or 0,
                    max_count=item.get("max_count"),
                    owner=owner or instance.owner,
                )
                for item in attrs_list
            ]
            if rules:
                AssetTypeAttribute.objects.bulk_create(rules, ignore_conflicts=False)

        return instance


class AssetReadSerializer(serializers.ModelSerializer):
    attributes = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = ('id',
                  'created_at',
                  'updated_at',
                  'title',
                  'asset_type',
                  'attributes',)

    def get_attributes(self, obj):
        return AssetTypeAttributeSerializer(obj.type_rules.all(), many=True).data


class AssetAttributeSerializer(serializers.Serializer):
    asset_type = serializers.CharField(write_only=True)
    asset_id = serializers.CharField(write_only=True)


class AttributeValuesSerializer(serializers.Serializer):
    attribute_id = serializers.CharField(write_only=True)
    value = serializers.CharField(write_only=True)

    def validate(self, attr):
        attribute_id = attr.get('attribute_id')
        value = attr.get('value')

        attribute = Attribute.objects.filter(pk=attribute_id).first()
        if not attribute:
            raise serializers.ValidationError('Attribute not found')

        property_type = attribute.property_type

        if property_type == 'int':
            attr['value_int'] = int(value)
        elif property_type == 'str':
            attr['value_str'] = str(value)
        attr.pop('value')
        # if not isinstance(value, property_type):
        #     raise serializers.ValidationError('Value is not a property type')

        return attr


class RelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation
        fields = ('id', 'created_at', 'updated_at', 'key', 'name', )


class AssetRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetRelation
        fields = ('relation',
                  # 'source_asset',
                  'target_asset',
                  'start_date',
                  'end_date',)


# class AssetAttributeValueSerializer(serializers.Serializer):
#     attribute_values = AttributeValuesSerializer(many=True)
#     relations = AssetRelationSerializer(many=True)
#     asset_id = serializers.CharField(write_only=True)
#
#     @transaction.atomic
#     def create(self, validated_data):
#         attribute_values = validated_data.pop('attribute_values')
#         relations = validated_data.pop('relations')
#         asset_id = validated_data.pop('asset_id')
#
#         asset = Asset.objects.get(id=asset_id)
#         for attribute_value in attribute_values:
#             obj = AssetAttributeValue.objects.create(asset=asset, **attribute_value)
#
#         for relation in relations:
#             AssetRelation.objects.create(source_asset=asset, **relation)
#
#         return obj

from collections import defaultdict
from django.db import transaction
from django.db.models import Count, Q
from rest_framework import serializers

from .models import Asset, Attribute, AssetAttributeValue, AssetRelation, Relation, AssetTypeAttribute


# ---------- Nested: Attribute Value (one-hot by property_type) ----------

class AttributeValueInSerializer(serializers.Serializer):
    attribute = serializers.PrimaryKeyRelatedField(queryset=Attribute.objects.all())
    value = serializers.JSONField()  # هرچی فرانت بده: str/int/float/bool/...
    status = serializers.ChoiceField(
        choices=AssetAttributeValue.Status.choices,
        required=False,
        default=AssetAttributeValue.Status.REGISTERED
    )

    # کش choices برای جلوگیری از کوئری تکراری
    _choices_cache: dict = {}

    def _coerce_int(self, v):
        if isinstance(v, bool):
            # جلوگیری از قبول شدن True/False به عنوان int
            raise serializers.ValidationError("مقدار عدد صحیح معتبر نیست.")
        try:
            if isinstance(v, (int,)):
                return int(v)
            if isinstance(v, float) and v.is_integer():
                return int(v)
            if isinstance(v, str):
                return int(v.strip())
        except (ValueError, TypeError):
            pass
        raise serializers.ValidationError("مقدار عدد صحیح معتبر نیست.")

    def _coerce_float(self, v):
        try:
            if isinstance(v, (int, float)):
                x = float(v)
            elif isinstance(v, str):
                s = v.strip().replace(",", ".")
                x = float(s)
            else:
                raise ValueError
            if x != x or x in (float("inf"), float("-inf")):
                raise ValueError
            return x
        except (ValueError, TypeError):
            raise serializers.ValidationError("مقدار عدد اعشاری معتبر نیست.")

    def _coerce_bool(self, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, (int,)):
            if v in (0, 1):
                return bool(v)
        if isinstance(v, str):
            s = v.strip().lower()
            if s in ("true", "yes", "on", "1"):
                return True
            if s in ("false", "no", "off", "0"):
                return False
        raise serializers.ValidationError("مقدار بولین معتبر نیست (true/false, 1/0, yes/no, on/off).")

    def _coerce_date(self, v):
        # ترجیح: ISO 8601
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            s = v.strip()
            # چند الگوی رایج
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    return datetime.strptime(s, fmt).date()
                except ValueError:
                    continue
            # تلاش نهایی: fromisoformat
            try:
                return date.fromisoformat(s)
            except ValueError:
                pass
        raise serializers.ValidationError("تاریخ معتبر نیست. فرمت پیشنهادی: YYYY-MM-DD")

    def _resolve_choice(self, attribute: Attribute, v):
        """
        v می‌تواند:
          - UUID pk (str)
          - internal value (attribute_choice.value)
          - label (attribute_choice.label)
        اولویت: pk → value__iexact → label__iexact
        """
        attr_id = attribute.id
        cache_key = f"{attr_id}"

        # کش لیست choices این attribute
        choices_qs = self._choices_cache.get(cache_key)
        # if choices_qs is None:
        #     choices_qs = list(AttributeChoice.objects.filter(attribute_id=attr_id))
        #     self._choices_cache[cache_key] = choices_qs

        # 1) pk
        if isinstance(v, str):
            for ch in choices_qs:
                if str(ch.id) == v:
                    return ch

        # 2) value__iexact
        if isinstance(v, str):
            matches = [ch for ch in choices_qs if ch.value.lower() == v.lower()]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                # بسیار نادر چون روی (attribute, value) کانسترینت یکتا داریم
                raise serializers.ValidationError("ابهام در انتخاب گزینه (value تکراری).")

        # 3) label__iexact
        if isinstance(v, str):
            matches = [ch for ch in choices_qs if (ch.label or "").lower() == v.lower()]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise serializers.ValidationError("ابهام در انتخاب گزینه (label چندتایی).")

        raise serializers.ValidationError("گزینه‌ی معتبر برای این خصیصه یافت نشد.")

    def validate(self, attrs):
        attr: Attribute = attrs["attribute"]
        ptype = attr.property_type
        v = attrs.get("value", None)

        if ptype == Attribute.PropertyType.INT:
            coerced = self._coerce_int(v)
            attrs["value_int"] = coerced

        elif ptype == Attribute.PropertyType.FLOAT:
            coerced = self._coerce_float(v)
            attrs["value_float"] = coerced

        elif ptype == Attribute.PropertyType.STR:
            # برای رشته، هر ورودی رو به str تبدیل کن؛ None مجاز نیست
            if v is None:
                raise serializers.ValidationError({"value": "برای نوع رشته مقدار لازم است."})
            attrs["value_str"] = str(v)

        elif ptype == Attribute.PropertyType.BOOL:
            coerced = self._coerce_bool(v)
            attrs["value_bool"] = coerced

        elif ptype == Attribute.PropertyType.DATE:
            coerced = self._coerce_date(v)
            attrs["value_date"] = coerced

        elif ptype == Attribute.PropertyType.CHOICE:
            if v is None or (isinstance(v, str) and not v.strip()):
                raise serializers.ValidationError({"value": "انتخاب گزینه الزامی است."})
            choice_obj = self._resolve_choice(attr, v)
            attrs["choice"] = choice_obj

        else:
            raise serializers.ValidationError({"attribute": "property_type نامعتبر است."})

        # value ورودی فقط برای تصمیم‌گیری بود؛ حذفش می‌کنیم تا به DB نرسه
        attrs.pop("value", None)
        return attrs


# ---------- Nested: Relation ----------

class AssetRelationWriteSerializer(serializers.ModelSerializer):
    relation = serializers.PrimaryKeyRelatedField(queryset=Relation.objects.all())
    target_asset = serializers.PrimaryKeyRelatedField(queryset=Asset.objects.all())

    class Meta:
        model = AssetRelation
        fields = ("relation", "target_asset", "start_date", "end_date", "note")

    def validate(self, attrs):
        st, en = attrs.get("start_date"), attrs.get("end_date")
        if st and en and en < st:
            raise serializers.ValidationError({"end_date": "نباید قبل از start_date باشد."})
        return attrs


# ---------- Wrapper: POST (append) / PUT (replace-all) ----------

class AssetAttributeValueUpsertSerializer(serializers.Serializer):
    asset = serializers.PrimaryKeyRelatedField(queryset=Asset.objects.all(), write_only=True)
    attribute_values = AttributeValueInSerializer(many=True, required=False)
    relations = AssetRelationWriteSerializer(many=True, required=False)

    # --- ابزار ولیدیشن قوانین type_rules ---
    def _validate_rules_and_counts(self, *, asset: Asset, incoming: list, replace_all: bool):
        """
        - asset.type_rules تعیین‌کننده‌ی مجاز بودن attribute و قوانین min/max/required/is_multi است.
        - در POST: final_count = existing + incoming
        - در PUT (replace_all): final_count = incoming (چون قبلش حذف می‌کنیم)
        """
        rules = {r.attribute_id: r for r in asset.type_rules.select_related("attribute")}
        # گروه‌بندی ورودی‌ها بر اساس attribute
        incoming_by_attr = defaultdict(list)
        for item in incoming:
            incoming_by_attr[item["attribute"].id].append(item)

        # برای هر خصیصه‌ای که داده آمده:
        for attr_id, items in incoming_by_attr.items():
            rule = rules.get(attr_id)
            if not rule:
                raise serializers.ValidationError({"attribute_values": f"خصیصه‌ی {attr_id} برای این دارایی مجاز نیست."})

            incoming_count = len(items)
            if replace_all:
                final_count = incoming_count
            else:
                existing_count = AssetAttributeValue.objects.filter(asset=asset, attribute_id=attr_id).count()
                final_count = existing_count + incoming_count

            # is_multi
            if not rule.is_multi and final_count > 1:
                raise serializers.ValidationError({
                    "attribute_values": f"خصیصه‌ی {rule.attribute.title} تک‌مقداری است (final_count={final_count})."
                })

            # min/max و required
            min_needed = max(1, rule.min_count) if rule.is_required else (rule.min_count or 0)
            if final_count < min_needed:
                raise serializers.ValidationError({
                    "attribute_values": f"برای {rule.attribute.title} حداقل {min_needed} مقدار لازم است (final={final_count})."
                })
            if rule.max_count is not None and final_count > rule.max_count:
                raise serializers.ValidationError({
                    "attribute_values": f"برای {rule.attribute.title} حداکثر {rule.max_count} مقدار مجاز است (final={final_count})."
                })

        # همچنین می‌تونیم اطمینان بدهیم برای requiredهایی که اصلاً در ورودی نیامده‌اند،
        # در POST جمع موجود+جدید حداقل یکی باشد. برای replace_all (PUT) باید صفر نشود.
        required_rules = [r for r in rules.values() if r.is_required]
        if replace_all:
            # همه‌چیز را جایگزین می‌کنیم؛ پس برای requiredهایی که اصلاً در ورودی نیستند، خطا بده
            for r in required_rules:
                if r.attribute_id not in incoming_by_attr and (r.min_count or 1) > 0:
                    raise serializers.ValidationError({
                        "attribute_values": f"خصیصه‌ی اجباری {r.attribute.title} ارسال نشده است."
                    })
        else:
            # در POST: اگر required است و موجودی صفر و در ورودی هم نیامده، خطا
            for r in required_rules:
                if r.attribute_id not in incoming_by_attr:
                    existing_count = AssetAttributeValue.objects.filter(
                        asset=asset, attribute_id=r.attribute_id
                    ).count()
                    if existing_count < max(1, r.min_count or 0):
                        raise serializers.ValidationError({
                            "attribute_values": f"برای {r.attribute.title} حداقل یک مقدار لازم است."
                        })

    # --- CREATE (POST: append) ---
    @transaction.atomic
    def create(self, validated_data):
        asset: Asset = validated_data["asset"]
        owner = self.context.get("owner")
        av_items = validated_data.get("attribute_values") or []
        rel_items = validated_data.get("relations") or []

        # قوانین را بر اساس append چک کن
        self._validate_rules_and_counts(asset=asset, incoming=av_items, replace_all=False)

        # ساخت مقادیر
        values_to_create = []
        for item in av_items:
            values_to_create.append(AssetAttributeValue(
                asset=asset,
                attribute=item["attribute"],
                value_int=item.get("value_int"),
                value_float=item.get("value_float"),
                value_str=item.get("value_str"),
                value_bool=item.get("value_bool"),
                value_date=item.get("value_date"),
                choice=item.get("choice"),
                status=item.get("status", AssetAttributeValue.Status.REGISTERED),
                owner=owner,
            ))
        if values_to_create:
            AssetAttributeValue.objects.bulk_create(values_to_create)

        # ساخت روابط
        rel_to_create = []
        for r in rel_items:
            rel_to_create.append(AssetRelation(
                relation=r["relation"],
                source_asset=asset,
                target_asset=r["target_asset"],
                start_date=r.get("start_date"),
                end_date=r.get("end_date"),
                note=r.get("note"),
                owner=owner,
            ))
        if rel_to_create:
            AssetRelation.objects.bulk_create(rel_to_create)

        return {
            "created_values": len(values_to_create),
            "created_relations": len(rel_to_create),
        }

    # --- UPDATE (PUT: replace-all) ---
    @transaction.atomic
    def update(self, asset: Asset, validated_data):
        owner = self.context.get("owner")
        av_items = validated_data.get("attribute_values") or []
        rel_items = validated_data.get("relations") or []

        # قوانین را بر اساس replace-all چک کن
        self._validate_rules_and_counts(asset=asset, incoming=av_items, replace_all=True)

        # جایگزینی کامل AAVها
        AssetAttributeValue.objects.filter(asset=asset).delete()
        values_to_create = []
        for item in av_items:
            values_to_create.append(AssetAttributeValue(
                asset=asset,
                attribute=item["attribute"],
                value_int=item.get("value_int"),
                value_float=item.get("value_float"),
                value_str=item.get("value_str"),
                value_bool=item.get("value_bool"),
                value_date=item.get("value_date"),
                choice=item.get("choice"),
                status=item.get("status", AssetAttributeValue.Status.REGISTERED),
                owner=owner,
            ))
        if values_to_create:
            AssetAttributeValue.objects.bulk_create(values_to_create)

        # جایگزینی کامل روابط (از این دارایی به دیگران)
        AssetRelation.objects.filter(source_asset=asset).delete()
        rel_to_create = []
        for r in rel_items:
            rel_to_create.append(AssetRelation(
                relation=r["relation"],
                source_asset=asset,
                target_asset=r["target_asset"],
                start_date=r.get("start_date"),
                end_date=r.get("end_date"),
                note=r.get("note"),
                owner=owner,
            ))
        if rel_to_create:
            AssetRelation.objects.bulk_create(rel_to_create)

        return {
            "replaced_values": len(values_to_create),
            "replaced_relations": len(rel_to_create),
        }



def render_aav_value(aav: AssetAttributeValue):
    # if aav.choice_id:
    #     return aav.choice.label or aav.choice.value
    if aav.value_int is not None:
        return aav.value_int
    if aav.value_float is not None:
        return aav.value_float
    if aav.value_bool is not None:
        return aav.value_bool
    if aav.value_date is not None:
        return aav.value_date.isoformat()
    return aav.value_str


class AssetRelationReadSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    target_asset = serializers.CharField(source="target_asset.title")

    class Meta:
        model = AssetRelation
        fields = ("relation", "target_asset", "start_date", "end_date")

    def get_relation(self, obj):
        return obj.relation.name or obj.relation.key


class AssetValuesResponseSerializer(serializers.Serializer):
    """
    ورودی: instance = Asset
    context:
      - values: QuerySet[AssetAttributeValue] با select_related کامل
      - relations: QuerySet[AssetRelation] فیلتر شده برای همون Asset
      - ordering: "category" یا "attribute" (اختیاری)
      - category_label_field: "key" یا "value" (اختیاری، پیش‌فرض key)
    """
    asset_title = serializers.SerializerMethodField()
    attribute_values = serializers.SerializerMethodField()
    relations = serializers.SerializerMethodField()

    def get_asset_title(self, asset):
        return asset.title

    def get_attribute_values(self, asset):
        from collections import OrderedDict, defaultdict

        values_qs = self.context.get("values")
        if values_qs is None:
            return []

        cat_label_field = self.context.get("category_label_field", "title")
        # tmp_bucket: cat_label -> attr_title -> [values]
        tmp_bucket = defaultdict(lambda: defaultdict(list))

        for aav in values_qs:
            category = aav.attribute.category
            if category:
                cat_label = getattr(category, cat_label_field, None) or category.title
            else:
                cat_label = "uncategorized"

            attr_title = aav.attribute.title
            tmp_bucket[cat_label][attr_title].append(render_aav_value(aav))

        # به فرمت نهایی تبدیل کن: [ {cat: [ {attr: val}, ... ]}, ... ]
        grouped = OrderedDict()
        for cat_label, attr_map in tmp_bucket.items():
            items = []
            for attr_title, values in attr_map.items():
                val = values[0] if len(values) == 1 else values
                items.append({attr_title: val})
            grouped[cat_label] = items

        return [{cat: items} for cat, items in grouped.items()]

    def get_relations(self, asset):
        relations_qs = self.context.get("relations")
        if relations_qs is None:
            return []
        return AssetRelationReadSerializer(relations_qs, many=True).data


class AssetUnitDetailSerializer(serializers.Serializer):
    unit_id = serializers.IntegerField(source="id")
    unit_label = serializers.CharField(source="label", allow_null=True)
    unit_code = serializers.CharField(source="code", allow_null=True)
    asset_title = serializers.CharField(source="asset.title")

    attribute_values = serializers.SerializerMethodField()
    relations = serializers.SerializerMethodField()

    def get_attribute_values(self, unit):
        from collections import OrderedDict, defaultdict

        values_qs = self.context.get("values")
        if not values_qs:
            return []

        cat_label_field = self.context.get("category_label_field", "title")

        tmp_bucket = defaultdict(lambda: defaultdict(list))

        for aav in values_qs:
            category = aav.attribute.category
            if category:
                cat_label = getattr(category, cat_label_field, None) or category.title
            else:
                cat_label = "uncategorized"

            attr_title = aav.attribute.title
            tmp_bucket[cat_label][attr_title].append(render_aav_value(aav))

        grouped = OrderedDict()
        for cat_label, attr_map in tmp_bucket.items():
            items = []
            for attr_title, values in attr_map.items():
                val = values[0] if len(values) == 1 else values
                items.append({attr_title: val})
            grouped[cat_label] = items

        return [{cat: items} for cat, items in grouped.items()]

    def get_relations(self, unit):
        relations_qs = self.context.get("relations")
        if not relations_qs:
            return []
        return AssetRelationReadSerializer(relations_qs, many=True).data


# --------------- Upload --------------------


class CsvUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    has_header = serializers.BooleanField(required=False, default=True)
    delimiter = serializers.CharField(required=False, default=",", max_length=4)

    def validate(self, attrs):
        f = attrs["file"]
        if not f.name.lower().endswith((".csv", ".txt")):
            raise serializers.ValidationError({"file": "فقط فایل CSV/TXT مجاز است."})
        return attrs


class CsvMappingSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    asset_column = serializers.CharField()
    asset_lookup_field = serializers.ChoiceField(choices=[("id","id"),("code","code"),("title","title")], default="id")
    attribute_map = serializers.DictField(
        child=serializers.UUIDField(), allow_empty=False
    )


class CsvEditRowsSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    # rows: [{"row_index": 12, "values": {"colA":"...", "colB":"..."}}]
    rows = serializers.ListField(
        child=serializers.DictField(), allow_empty=False
    )


class CsvCommitSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    mode = serializers.ChoiceField(choices=[("append","append"),("replace","replace")], default="append")


# ***********************************************************************************************************************


# serializers.py
from rest_framework import serializers
from django.db import transaction
from datetime import datetime
import json
import jdatetime

from .models import Asset, AssetUnit, Attribute, AssetTypeAttribute, AssetAttributeValue


class AssetUnitSerializer(serializers.ModelSerializer):
    asset = serializers.CharField(source="asset.title", read_only=True)
    owner = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = AssetUnit
        fields = ('id',
                  'created_at',
                  'updated_at',
                  'label',
                  'asset',
                  'code',
                  'is_active',
                  'is_registered',
                  'owner')


def parse_choices(attr: Attribute) -> set:
    if not attr.choices: return set()
    s = attr.choices.strip()
    try:
        data = json.loads(s)
        if isinstance(data, list):
            return set(map(lambda x: str(x).strip(), data))
    except Exception:
        pass
    parts = []
    for line in s.splitlines():
        parts += line.split(',')
    return set(p.strip() for p in parts if p.strip())

def to_bool(v):
    if isinstance(v, bool): return v
    if isinstance(v, (int, float)): return bool(v)
    return str(v).strip().lower() in ('1','true','t','yes','y','on','ok','✔','✓')

class AssetUnitCreateSerializer(serializers.Serializer):
    asset_id   = serializers.PrimaryKeyRelatedField(queryset=Asset.objects.all(), source='asset')
    label      = serializers.CharField(required=False, allow_blank=True)
    code       = serializers.CharField(required=False, allow_blank=True)
    attributes = serializers.DictField(child=serializers.JSONField(), required=True)
    relations  = serializers.ListField(  # اضافه شد
        child=serializers.DictField(),   # هر رابطه به صورت dict
        required=False
    )
    # مثال attributes: {"12":"HP", "13":35, "16":["duplex","wifi"]}

    def validate(self, data):
        asset: Asset = data['asset']
        attrs = data['attributes'] or {}

        # قوانین همین Asset (required/is_multi/min/max)
        rules_qs = (AssetTypeAttribute.objects
                    .select_related('attribute')
                    .filter(asset=asset))
        if not rules_qs.exists():
            raise serializers.ValidationError("برای این دارایی هیچ قانون خصیصه‌ای تعریف نشده.")

        rules = {str(r.attribute_id): r for r in rules_qs}
        required_ids = {str(r.attribute_id) for r in rules_qs if r.is_required}

        # required → باید در ورودی باشد
        missing = required_ids - set(attrs.keys())
        if missing:
            raise serializers.ValidationError({"attributes": f"خصیصه‌های اجباری تامین نشد: {sorted(missing)}"})

        # هیچ خصیصهٔ خارج از rule نباشد
        invalid = [k for k in attrs.keys() if k not in rules]
        if invalid:
            raise serializers.ValidationError({"attributes": f"attribute_id نامعتبر: {invalid}"})

        # تایپ/چویس‌ها
        for attr_id, val in attrs.items():
            r = rules[attr_id]
            a = r.attribute
            p = a.property_type

            if p == Attribute.PropertyType.INT:
                try: int(val)
                except: raise serializers.ValidationError({attr_id: "باید عدد صحیح باشد"})
            elif p == Attribute.PropertyType.FLOAT:
                try: float(val)
                except: raise serializers.ValidationError({attr_id: "باید عدد اعشاری باشد"})
            elif p == Attribute.PropertyType.BOOL:
                _ = to_bool(val)
            elif p == Attribute.PropertyType.DATE:
                date_str = str(val)
                try:
                    jdate = jdatetime.datetime.strptime(date_str, "%Y/%m/%d")  # 1404/06/19
                    gdate = jdate.togregorian().date()  # تبدیل به میلادی
                except ValueError:
                    raise serializers.ValidationError({attr_id: "تاریخ باید به فرمت YYYY/MM/DD (شمسی) باشد"})

            else:  # STR
                if val is None:
                    raise serializers.ValidationError({attr_id: "باید مقدار متنی بدهید"})

            # single نباید لیست باشد
            if not r.is_multi and isinstance(val, (list, tuple)):
                raise serializers.ValidationError({attr_id: "این خصیصه تک‌مقداری است؛ لیست ندهید"})

        data['_rules'] = rules
        return data

    @transaction.atomic
    def create(self, vd):
        asset: Asset = vd['asset']
        label = vd.get('label') or None
        code  = vd.get('code') or None
        attrs = vd['attributes']
        rules = vd['_rules']
        rels  = vd.get('relations') or []

        # 1) ساخت یک Unit
        unit = AssetUnit.objects.create(
            asset=asset, label=label, code=code,
            is_active=True, is_registered=True
        )

        # 2) نوشتن EAV برای همین Unit
        rows = []
        def add(attr, p, val):
            row = dict(asset=asset, unit=unit, attribute=attr)
            if p == Attribute.PropertyType.INT:     row['value_int']   = int(val)
            elif p == Attribute.PropertyType.FLOAT: row['value_float'] = float(val)
            elif p == Attribute.PropertyType.BOOL:  row['value_bool']  = to_bool(val)
            elif p == Attribute.PropertyType.DATE:
                jdate = jdatetime.datetime.strptime(str(val), "%Y/%m/%d")
                gdate = jdate.togregorian().date()  # تبدیل به میلادی
                row['value_date']  = gdate
            elif p == Attribute.PropertyType.CHOICE:row['choice']      = str(val)
            else:                                   row['value_str']   = str(val)
            rows.append(AssetAttributeValue(**row))

        for attr_id, val in attrs.items():
            rule = rules[attr_id]
            a = rule.attribute
            if rule.is_multi and a.property_type == Attribute.PropertyType.CHOICE:
                for v in val: add(a, a.property_type, v)
            else:
                add(a, a.property_type, val)

        AssetAttributeValue.objects.bulk_create(rows, batch_size=500)

        rel_objs = []
        for r in rels:
            rel_objs.append(AssetRelation(
                end_date=r.get("end_date"),
                relation_id=r.get("relation"),
                start_date=r.get("start_date"),
                target_asset_id=r.get("target_asset"),
                source_asset=unit,
            ))
        if rel_objs:
            AssetRelation.objects.bulk_create(rel_objs, batch_size=200)
        return unit








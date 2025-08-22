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
                  'key',
                  'value')


class AttributeSerializer(serializers.ModelSerializer):
    category_value = serializers.CharField(source='category.value')

    class Meta:
        model = Attribute
        fields = ('id',
                  'created_at',
                  'updated_at',
                  'title',
                  'title_en',
                  'property_type',
                  'category',
                  'category_value',)


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

from .models import (
    Asset, Attribute, AttributeChoice,
    AssetAttributeValue, AssetRelation, Relation, AssetTypeAttribute
)


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
        if choices_qs is None:
            choices_qs = list(AttributeChoice.objects.filter(attribute_id=attr_id))
            self._choices_cache[cache_key] = choices_qs

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
    if aav.choice_id:
        return aav.choice.label or aav.choice.value
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

        cat_label_field = self.context.get("category_label_field", "key")
        # tmp_bucket: cat_label -> attr_title -> [values]
        tmp_bucket = defaultdict(lambda: defaultdict(list))

        for aav in values_qs:
            category = aav.attribute.category
            if category:
                cat_label = getattr(category, cat_label_field, None) or category.key
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


class AttributeChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeChoice
        fields = ("id", "attribute", "value", "label", "created_at", "updated_at")

    def validate(self, attrs):
        attribute = attrs.get("attribute") or getattr(self.instance, "attribute", None)
        value = attrs.get("value") or getattr(self.instance, "value", None)

        if attribute and value:
            qs = AttributeChoice.objects.filter(attribute=attribute, value__iexact=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"value": "این مقدار برای این خصیصه از قبل وجود دارد."})
        return attrs














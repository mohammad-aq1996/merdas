from datetime import datetime, date
from collections import defaultdict
import jdatetime

from rest_framework import serializers

from django.db.models import Count, Q
from django.db import transaction

from assets.models import *


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
        fields = ("attribute", "is_required", "is_multi")


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
    if aav.choice is not None:
        return aav.choice
    return aav.value_str


class AssetRelationReadSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    target_asset = serializers.CharField(source="target_asset.label")

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


class AssetUnitUpsertSerializer(serializers.Serializer):
    # روی create لازم، روی update از instance گرفته می‌شود و تغییرش ممنوع است
    asset_id   = serializers.PrimaryKeyRelatedField(queryset=Asset.objects.all(),
                                                    source='asset', required=False)
    label      = serializers.CharField(required=False, allow_blank=True)
    code       = serializers.CharField(required=False, allow_blank=True)

    # روی create اجباری؛ روی update اختیاری
    attributes = serializers.DictField(child=serializers.JSONField(), required=False)

    # CRUD روابط (create/update/delete)، مثل قبل
    relations  = serializers.ListField(child=serializers.DictField(), required=False)
    relations_mode = serializers.ChoiceField(choices=['patch', 'replace'], required=False, default='patch')

    # ===== helpers
    def _mode(self):
        return 'create' if self.instance is None else 'update'

    def _parse_jalali_date(self, s):
        return jdatetime.datetime.strptime(str(s), "%Y/%m/%d").date()

    def _to_bool(self, v):
        if isinstance(v, bool): return v
        if isinstance(v, str): return v.strip().lower() in ("true","1","yes","y","on","بله")
        return bool(v)

    # ===== validate
    def validate(self, data):
        mode = self._mode()

        # asset را تعیین کن
        asset = data.get('asset') if mode == 'create' else (data.get('asset') or self.instance.asset)
        if mode == 'update' and 'asset' in data and data['asset'] != self.instance.asset:
            raise serializers.ValidationError({"asset_id": "تغییر دارایی برای یک یونیت مجاز نیست."})

        # قوانین
        rules_qs = (AssetTypeAttribute.objects
                    .select_related('attribute')
                    .filter(asset=asset))
        if not rules_qs.exists():
            raise serializers.ValidationError("برای این دارایی هیچ قانون خصیصه‌ای تعریف نشده.")
        rules = {str(r.attribute_id): r for r in rules_qs}
        required_ids = {str(r.attribute_id) for r in rules_qs if r.is_required}

        attrs = data.get('attributes', None)

        # برای update نیاز به current داریم تا required بعد از merge بررسی شود
        current = {}
        if mode == 'update':
            by_attr = {}
            for row in AssetAttributeValue.objects.filter(unit=self.instance).select_related('attribute'):
                by_attr.setdefault(str(row.attribute_id), []).append(row)
            for aid, rows in by_attr.items():
                a = rows[0].attribute
                p = a.property_type
                if len(rows) > 1 and p == Attribute.PropertyType.CHOICE:
                    current[aid] = [r.choice for r in rows]
                else:
                    if p == Attribute.PropertyType.INT:     current[aid] = rows[0].value_int
                    elif p == Attribute.PropertyType.FLOAT: current[aid] = rows[0].value_float
                    elif p == Attribute.PropertyType.BOOL:  current[aid] = rows[0].value_bool
                    elif p == Attribute.PropertyType.DATE:  current[aid] = rows[0].value_date
                    elif p == Attribute.PropertyType.CHOICE:current[aid] = rows[0].choice
                    else:                                   current[aid] = rows[0].value_str

        effective = ({**current, **attrs} if attrs is not None else (current if mode=='update' else {}))

        # الزامات
        if mode == 'create':
            if attrs is None:
                raise serializers.ValidationError({"attributes": "ارسال attributes در ایجاد الزامی است."})
            missing = required_ids - set(effective.keys())
            if missing:
                raise serializers.ValidationError({"attributes": f"خصیصه‌های اجباری تامین نشد: {sorted(missing)}"})
        else:
            if attrs is not None:
                missing = required_ids - set(effective.keys())
                if missing:
                    raise serializers.ValidationError({"attributes": f"خصیصه‌های اجباری تامین نشد: {sorted(missing)}"})

        # اعتبارسنجی فقط روی attrهای ارسال‌شده
        if attrs is not None:
            invalid = [k for k in attrs.keys() if k not in rules]
            if invalid:
                raise serializers.ValidationError({"attributes": f"attribute_id نامعتبر: {invalid}"})

            for attr_id, val in attrs.items():
                r = rules[attr_id]
                a = r.attribute
                p = a.property_type

                if not r.is_multi and isinstance(val, (list, tuple)):
                    raise serializers.ValidationError({attr_id: "این خصیصه تک‌مقداری است؛ لیست ندهید"})

                try:
                    if p == Attribute.PropertyType.INT:
                        int(val)
                    elif p == Attribute.PropertyType.FLOAT:
                        float(val)
                    elif p == Attribute.PropertyType.BOOL:
                        self._to_bool(val)
                    elif p == Attribute.PropertyType.DATE:
                        self._parse_jalali_date(val)
                    else:  # STR/CHOICE
                        if val is None:
                            raise ValueError()
                except Exception:
                    msg = "مقدار نامعتبر"
                    if p == Attribute.PropertyType.INT:   msg = "باید عدد صحیح باشد"
                    if p == Attribute.PropertyType.FLOAT: msg = "باید عدد اعشاری باشد"
                    if p == Attribute.PropertyType.DATE:  msg = "تاریخ باید YYYY/MM/DD (شمسی) باشد"
                    raise serializers.ValidationError({attr_id: msg})

        # روابط (در صورت ارسال)
        rels = data.get('relations', None)
        if rels is not None:
            for i, r in enumerate(rels, start=1):
                if r.get("_delete") and not r.get("id"):
                    continue
                if r.get("target_asset") and not AssetUnit.objects.filter(pk=r["target_asset"]).exists():
                    raise serializers.ValidationError({"relations": f"[{i}] target_asset نامعتبر"})
                if r.get("relation") and not Relation.objects.filter(pk=r["relation"]).exists():
                    raise serializers.ValidationError({"relations": f"[{i}] relation نامعتبر"})


        data["_rules"] = rules
        data["_asset"] = asset
        return data

    # ===== persistence
    @transaction.atomic
    def create(self, vd):
        asset = vd["_asset"]
        label = vd.get('label') or None
        code  = vd.get('code') or None
        attrs = vd.get('attributes') or {}
        rules = vd["_rules"]
        rels  = vd.get('relations') or []

        unit = AssetUnit.objects.create(
            asset=asset, label=label, code=code,
            is_active=True, is_registered=True
        )

        rows = []
        def add_row(a, p, v):
            row = {"asset": asset, "unit": unit, "attribute": a}
            if p == Attribute.PropertyType.INT:      row["value_int"]   = int(v)
            elif p == Attribute.PropertyType.FLOAT:  row["value_float"] = float(v)
            elif p == Attribute.PropertyType.BOOL:   row["value_bool"]  = self._to_bool(v)
            elif p == Attribute.PropertyType.DATE:   row["value_date"]  = self._parse_jalali_date(v)
            elif p == Attribute.PropertyType.CHOICE: row["choice"]      = str(v)
            else:                                    row["value_str"]   = str(v)
            rows.append(AssetAttributeValue(**row))

        for attr_id, val in attrs.items():
            rule = rules[attr_id]
            a, p = rule.attribute, rule.attribute.property_type
            if rule.is_multi and p == Attribute.PropertyType.CHOICE:
                for v in (val or []): add_row(a, p, v)
            else:
                add_row(a, p, val)
        if rows:
            AssetAttributeValue.objects.bulk_create(rows, batch_size=500)

        rel_objs = []
        for r in (rels or []):
            rel_objs.append(AssetRelation(
                source_asset=unit,
                relation_id=r.get("relation"),
                target_asset_id=r.get("target_asset"),
                start_date=r.get("start_date"),
                end_date=r.get("end_date")
            ))
        if rel_objs:
            AssetRelation.objects.bulk_create(rel_objs, batch_size=200)

        return unit

    @transaction.atomic
    def update(self, unit: AssetUnit, vd):
        unit = AssetUnit.objects.select_for_update().get(pk=unit.pk)

        if "label" in vd: unit.label = vd.get("label") or None
        if "code"  in vd: unit.code  = vd.get("code") or None
        unit.is_registered = True
        unit.save(update_fields=["label", "code", "is_registered"])

        rules = vd["_rules"]

        # attributes فقط اگر ارسال شده باشند
        attrs = vd.get("attributes", None)
        if attrs is not None:
            for attr_id, val in attrs.items():
                rule = rules[attr_id]
                a, p = rule.attribute, rule.attribute.property_type
                AssetAttributeValue.objects.filter(unit=unit, attribute_id=a.id).delete()

                rows = []
                def add(v):
                    row = {"asset": unit.asset, "unit": unit, "attribute": a}
                    if p == Attribute.PropertyType.INT:      row["value_int"]   = int(v)
                    elif p == Attribute.PropertyType.FLOAT:  row["value_float"] = float(v)
                    elif p == Attribute.PropertyType.BOOL:   row["value_bool"]  = self._to_bool(v)
                    elif p == Attribute.PropertyType.DATE:   row["value_date"]  = self._parse_jalali_date(v)
                    elif p == Attribute.PropertyType.CHOICE: row["choice"]      = str(v)
                    else:                                    row["value_str"]   = str(v)
                    rows.append(AssetAttributeValue(**row))

                if rule.is_multi and p == Attribute.PropertyType.CHOICE:
                    for v in (val or []): add(v)
                else:
                    add(val)
                if rows:
                    AssetAttributeValue.objects.bulk_create(rows, batch_size=500)

        # روابط
        rels = vd.get("relations", None)
        mode = vd.get("relations_mode", "patch")
        if rels is not None:
            if mode == "replace":
                AssetRelation.objects.filter(source_asset=unit).delete()

            for r in rels:
                rel_id = r.get("id")
                if r.get("_delete"):
                    if rel_id:
                        AssetRelation.objects.filter(id=rel_id, source_asset=unit).delete()
                    continue

                fields = {}
                if "relation" in r:     fields["relation_id"] = r["relation"]
                if "target_asset" in r: fields["target_asset_id"] = r["target_asset"]
                if "start_date" in r:   fields["start_date"] = r.get("start_date")
                if "end_date" in r:     fields["end_date"]   = r.get("end_date")

                if rel_id:
                    if fields:
                        AssetRelation.objects.filter(id=rel_id, source_asset=unit).update(**fields)
                else:
                    AssetRelation.objects.create(source_asset=unit, **fields)

        return unit


class CsvIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportIssue
        fields = "__all__"



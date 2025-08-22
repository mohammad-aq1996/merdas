from rest_framework import serializers
from assets.models import *
from django.db import transaction


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


class AssetAttributeValueSerializer(serializers.Serializer):
    attribute_values = AttributeValuesSerializer(many=True)
    relations = AssetRelationSerializer(many=True)
    asset_id = serializers.CharField(write_only=True)

    # class Meta:
    #     model = AssetAttributeValue
    #     fields = ('asset_id',
    #               'attribute_values',
    #               'relations',)

    @transaction.atomic
    def create(self, validated_data):
        attribute_values = validated_data.pop('attribute_values')
        relations = validated_data.pop('relations')
        asset_id = validated_data.pop('asset_id')

        asset = Asset.objects.get(id=asset_id)
        for attribute_value in attribute_values:
            obj = AssetAttributeValue.objects.create(asset=asset, **attribute_value)

        for relation in relations:
            AssetRelation.objects.create(source_asset=asset, **relation)

        return obj


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














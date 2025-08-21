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


class AssetCreateSerializer(serializers.ModelSerializer):
    attributes = AssetTypeAttributeSerializer(many=True)

    class Meta:
        model = Asset
        fields = ('title',
                  'asset_type',
                  'attributes',)

    def create(self, validated_data):
        attributes = validated_data.pop('attributes')
        asset = Asset.objects.create(**validated_data)
        for field in attributes:
            AssetTypeAttribute.objects.create(asset=asset, **field)
        return asset

    def update(self, instance, validated_data):
        attributes = validated_data.pop('attributes')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        instance.type_rules.all().delete()

        for field in attributes:
            AssetTypeAttribute.objects.create(asset=instance, **field)

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























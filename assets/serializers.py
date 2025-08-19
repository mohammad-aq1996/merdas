from rest_framework import serializers
from assets.models import *


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
        if not isinstance(value, property_type):
            raise serializers.ValidationError('Value is not a property type')

        return value


class RelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation
        fields = ('key', 'name', )


class AssetRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetRelation
        fields = ('relation',
                  # 'source_asset',
                  'target_asset',
                  'start_date',
                  'end_date',)


class AssetAttributeValueSerializer(serializers.Serializer):
    attribute_values = serializers.ListField(write_only=True, child=AttributeValuesSerializer())
    relations = serializers.ListField(write_only=True, child=RelationSerializer())

    class Meta:
        model = AssetAttributeValue
        fields = ('asset',
                  'attribute_values',
                  'relations',)

    def create(self, validated_data):
        attribute_values = validated_data.pop('attribute_value')
        relations = validated_data.pop('relations')
        asset = validated_data.pop('asset')

        for attribute_value in attribute_values:
            obj = AssetAttributeValue.objects.create(asset=asset, **attribute_value)

        for relation in relations:
            AssetRelation.objects.create(source_asset=asset, **relation)

        return obj























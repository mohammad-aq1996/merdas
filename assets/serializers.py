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
    category_title = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        fields = ('id',
                  'created_at',
                  'updated_at',
                  'title',
                  'title_en',
                  'property_type',
                  'category',
                  'category_title',)

    def get_category_title(self, obj):
        return obj.category.value


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








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
    class Meta:
        model = Attribute
        fields = ('id',
                  'created_at',
                  'updated_at',
                  'title',
                  'title_en',
                  'property_type',
                  'category')


class AssetTypeAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetTypeAttribute
        fields = ('attribute',
                  'is_required',
                  'is_multi',)


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











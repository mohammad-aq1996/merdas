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




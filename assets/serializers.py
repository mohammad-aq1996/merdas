from rest_framework import serializers
from assets.models import *


class AttributeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeCategory
        fields = ('id', 'created_at', 'updated_at', 'key', 'value')



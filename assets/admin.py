from django.contrib import admin
from .models import *


admin.site.register(AttributeCategory)
admin.site.register(Attribute)
admin.site.register(AttributeChoice)
admin.site.register(Asset)
admin.site.register(AssetTypeAttribute)
admin.site.register(AssetAttributeValue)
admin.site.register(Relation)
admin.site.register(AssetRelation)
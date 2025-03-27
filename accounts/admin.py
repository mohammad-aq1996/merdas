from django.contrib import admin
from accounts.models import *


admin.site.register(User)
admin.site.register(Role)
admin.site.register(UserGroup)

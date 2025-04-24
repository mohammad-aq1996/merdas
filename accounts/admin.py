from django.contrib import admin
from accounts.models import *
from core.models import *

admin.site.register(User)
admin.site.register(Role)
admin.site.register(UserGroup)
admin.site.register(LoginAttempt)
admin.site.register(IllPassword)
admin.site.register(IllUsername)
admin.site.register(Settings)

# init_admin.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = "admin2"
password = "admin1234"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, password=password)
    print("✅ سوپر یوزر ساخته شد.")
else:
    print("ℹ️ سوپر یوزر قبلاً وجود داشته.")

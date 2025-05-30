# Generated by Django 5.1.7 on 2025-04-24 16:27

import django_jalali.db.models
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', django_jalali.db.models.jDateTimeField(auto_now_add=True)),
                ('updated_at', django_jalali.db.models.jDateTimeField(auto_now=True)),
                ('config', models.JSONField(default=dict)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

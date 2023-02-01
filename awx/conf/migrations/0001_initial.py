# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings

import awx.main.fields


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('key', models.CharField(max_length=255)),
                ('value', awx.main.fields.JSONBlob(null=True)),
                (
                    'user',
                    models.ForeignKey(related_name='settings', default=None, editable=False, to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True),
                ),
            ],
            options={'abstract': False},
        )
    ]

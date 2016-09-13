# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0032_v302_credential_permissions_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='timeout',
            field=models.PositiveIntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='timeout',
            field=models.PositiveIntegerField(default=0, blank=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0032_v302_credential_permissions_update'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='instance',
            name='primary',
        ),
        migrations.AlterField(
            model_name='instance',
            name='uuid',
            field=models.CharField(max_length=40),
        ),
    ]

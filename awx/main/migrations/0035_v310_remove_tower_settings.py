# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import awx.main.models.notifications
import jsonfield.fields
import django.db.models.deletion
import awx.main.models.workflow
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0034_v310_release'),
    ]

    operations = [
        # Remove Tower settings, these settings are now in separate awx.conf app.
        migrations.RemoveField(
            model_name='towersettings',
            name='user',
        ),
        migrations.DeleteModel(
            name='TowerSettings',
        ),
    ]

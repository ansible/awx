# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


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

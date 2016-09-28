# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0035_v310_jobevent_uuid'),
    ]

    # These settings are now in the separate awx.conf app.
    operations = [
        migrations.RemoveField(
            model_name='towersettings',
            name='user',
        ),
        migrations.DeleteModel(
            name='TowerSettings',
        ),
    ]

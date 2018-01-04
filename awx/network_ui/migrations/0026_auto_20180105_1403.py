# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0025_devicehost_topologyinventory'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='devicehost',
            name='device',
        ),
        migrations.AddField(
            model_name='device',
            name='host_id',
            field=models.IntegerField(default=0),
        ),
        migrations.DeleteModel(
            name='DeviceHost',
        ),
    ]

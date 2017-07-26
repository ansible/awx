# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0005_topologyhistory_undone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topologyhistory',
            name='undone',
            field=models.BooleanField(default=False),
        ),
    ]

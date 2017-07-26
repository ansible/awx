# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prototype', '0002_remove_topology_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='type',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]

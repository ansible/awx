# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0014_group_topology'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupdevice',
            name='group',
            field=models.ForeignKey(to='network_ui.Group'),
        ),
    ]

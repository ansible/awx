# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0013_auto_20170710_1840'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='topology',
            field=models.ForeignKey(default=1, to='network_ui.Topology'),
            preserve_default=False,
        ),
    ]

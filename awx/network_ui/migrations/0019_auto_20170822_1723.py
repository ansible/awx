# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0018_auto_20170821_1557'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stream',
            name='from_device',
            field=models.ForeignKey(related_name='from_stream', to='network_ui.Device'),
        ),
        migrations.AlterField(
            model_name='stream',
            name='label',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='stream',
            name='to_device',
            field=models.ForeignKey(related_name='to_stream', to='network_ui.Device'),
        ),
    ]

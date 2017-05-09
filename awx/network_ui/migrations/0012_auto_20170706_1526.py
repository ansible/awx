# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0011_link_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='interface_id_seq',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='topology',
            name='device_id_seq',
            field=models.IntegerField(default=0, verbose_name=b'Topology'),
        ),
        migrations.AddField(
            model_name='topology',
            name='link_id_seq',
            field=models.IntegerField(default=0),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0019_auto_20170822_1723'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='process_id_seq',
            field=models.IntegerField(default=0),
        ),
    ]

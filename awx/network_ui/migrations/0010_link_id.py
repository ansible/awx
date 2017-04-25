# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prototype', '0009_auto_20170403_1912'),
    ]

    operations = [
        migrations.AddField(
            model_name='link',
            name='id',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]

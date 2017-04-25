# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prototype', '0007_auto_20170328_1655'),
    ]

    operations = [
        migrations.AddField(
            model_name='interface',
            name='id',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0034_v310_modify_ha_instance'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobevent',
            name='uuid',
            field=models.CharField(default=b'', max_length=1024, editable=False),
        ),
    ]

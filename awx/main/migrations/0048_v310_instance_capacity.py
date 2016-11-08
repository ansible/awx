# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0047_v310_tower_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='capacity',
            field=models.PositiveIntegerField(default=100, editable=False),
        ),
    ]

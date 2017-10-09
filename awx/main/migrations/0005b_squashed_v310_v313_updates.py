# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005a_squashed_v310_v313_updates'),
    ]

    replaces = [
        (b'main', '0037_v313_instance_version'),
    ]

    operations = [
        # Remove Tower settings, these settings are now in separate awx.conf app.
        migrations.AddField(
            model_name='instance',
            name='version',
            field=models.CharField(max_length=24, blank=True),
        ),
    ]

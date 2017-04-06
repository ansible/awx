# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0036_v311_insights'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventorysource',
            name='group',
        ),
    ]

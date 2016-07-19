# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_v300_prompting_migrations'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='host',
            options={'ordering': ('name',)},
        ),
    ]

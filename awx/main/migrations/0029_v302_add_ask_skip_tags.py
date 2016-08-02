# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0028_v300_org_team_cascade'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_skip_tags_on_launch',
            field=models.BooleanField(default=False),
        ),
    ]

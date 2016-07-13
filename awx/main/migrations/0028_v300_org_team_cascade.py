# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0027_v300_team_migrations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='organization',
            field=models.ForeignKey(related_name='teams', to='main.Organization', null=True),
        ),
    ]

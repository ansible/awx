# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0047_v310_tower_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowjob',
            name='survey_passwords',
            field=jsonfield.fields.JSONField(default={}, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='workflowjobtemplate',
            name='survey_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='workflowjobtemplate',
            name='survey_spec',
            field=jsonfield.fields.JSONField(default={}, blank=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0039_v310_channelgroup'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='artifacts',
            field=jsonfield.fields.JSONField(default={}, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='workflowjobnode',
            name='ancestor_artifacts',
            field=jsonfield.fields.JSONField(default={}, editable=False, blank=True),
        ),
    ]

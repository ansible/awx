# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0029_v302_add_ask_skip_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='survey_passwords',
            field=jsonfield.fields.JSONField(default={}, editable=False, blank=True),
        ),
    ]

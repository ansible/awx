# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_v320_drop_v1_credential_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowjobtemplate',
            name='ask_variables_on_launch',
            field=models.BooleanField(default=False),
        ),
    ]

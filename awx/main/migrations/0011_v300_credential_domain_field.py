# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_v300_create_system_job_templates'),
    ]

    operations = [
        migrations.AddField(
            model_name='credential',
            name='domain',
            field=models.CharField(default=b'', help_text='The identifier for the domain.', max_length=100, verbose_name='Domain', blank=True),
        ),
    ]

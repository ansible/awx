# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_v300_new_azure_credential'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='labels',
        ),
        migrations.RemoveField(
            model_name='jobtemplate',
            name='labels',
        ),
        migrations.AddField(
            model_name='unifiedjob',
            name='labels',
            field=models.ManyToManyField(related_name='unifiedjob_labels', to='main.Label', blank=True),
        ),
    ]

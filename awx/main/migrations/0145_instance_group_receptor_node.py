# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0144_event_partitions'),
    ]

    operations = [
        migrations.AddField(
            model_name='instancegroup',
            name='receptor_node',
            field=models.CharField(
                blank=True,
                default=None,
                help_text='Receptor node to send all jobs to from this instance group',
                max_length=40,
                null=True,
            ),
        ),
    ]

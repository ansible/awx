# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_v330_move_deprecated_stdout'),
    ]

    operations = [
        migrations.AddField(
            model_name='instancegroup',
            name='policy_instance_list',
            field=awx.main.fields.JSONField(default=[], help_text='List of exact-match Instances that will always be automatically assigned to this group',
                                            blank=True),
        ),
        migrations.AddField(
            model_name='instancegroup',
            name='policy_instance_minimum',
            field=models.IntegerField(default=0, help_text='Static minimum number of Instances to automatically assign to this group'),
        ),
        migrations.AddField(
            model_name='instancegroup',
            name='policy_instance_percentage',
            field=models.IntegerField(default=0, help_text='Percentage of Instances to automatically assign to this group'),
        ),
    ]

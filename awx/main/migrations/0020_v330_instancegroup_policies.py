# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from decimal import Decimal
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_v330_custom_virtualenv'),
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
        migrations.AddField(
            model_name='instance',
            name='capacity_adjustment',
            field=models.DecimalField(decimal_places=2, default=Decimal('1.0'), max_digits=3),
        ),
        migrations.AddField(
            model_name='instance',
            name='cpu',
            field=models.IntegerField(default=0, editable=False)
        ),
        migrations.AddField(
            model_name='instance',
            name='memory',
            field=models.BigIntegerField(default=0, editable=False)
        ),
        migrations.AddField(
            model_name='instance',
            name='cpu_capacity',
            field=models.IntegerField(default=0, editable=False)
        ),
        migrations.AddField(
            model_name='instance',
            name='mem_capacity',
            field=models.IntegerField(default=0, editable=False)
        ),
        migrations.AddField(
            model_name='instance',
            name='enabled',
            field=models.BooleanField(default=True)
        )
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_v300_labels_changes'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitystream',
            name='role',
            field=models.ManyToManyField(to='main.Role', blank=True),
        ),
    ]

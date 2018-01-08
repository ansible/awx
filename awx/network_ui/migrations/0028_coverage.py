# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0027_eventtrace'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coverage',
            fields=[
                ('coverage_id', models.AutoField(serialize=False, primary_key=True)),
                ('trace_session_id', models.IntegerField()),
                ('coverage_data', models.TextField()),
                ('client', models.ForeignKey(to='network_ui.Client')),
            ],
        ),
    ]

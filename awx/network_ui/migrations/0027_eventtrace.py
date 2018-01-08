# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0026_auto_20180105_1403'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventTrace',
            fields=[
                ('event_trace_id', models.AutoField(serialize=False, primary_key=True)),
                ('trace_session_id', models.IntegerField(default=0)),
                ('event_data', models.TextField()),
                ('message_id', models.IntegerField()),
                ('client', models.ForeignKey(to='network_ui.Client')),
            ],
        ),
    ]

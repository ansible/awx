# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0021_toolbox_toolboxitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='FSMTrace',
            fields=[
                ('fsm_trace_id', models.AutoField(serialize=False, primary_key=True)),
                ('fsm_name', models.CharField(max_length=200)),
                ('from_state', models.CharField(max_length=200)),
                ('to_state', models.CharField(max_length=200)),
                ('message_type', models.CharField(max_length=200)),
                ('trace_session_id', models.IntegerField(default=0)),
                ('order', models.IntegerField(default=0)),
                ('client', models.ForeignKey(to='network_ui.Client')),
            ],
        ),
    ]

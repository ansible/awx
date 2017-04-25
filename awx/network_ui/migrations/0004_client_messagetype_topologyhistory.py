# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0003_device_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('client_id', models.AutoField(serialize=False, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='MessageType',
            fields=[
                ('message_type_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='TopologyHistory',
            fields=[
                ('topology_history_id', models.AutoField(serialize=False, primary_key=True)),
                ('message_id', models.IntegerField()),
                ('message_data', models.TextField()),
                ('client', models.ForeignKey(to='network_ui.Client')),
                ('message_type', models.ForeignKey(to='network_ui.MessageType')),
                ('topology', models.ForeignKey(to='network_ui.Topology')),
            ],
        ),
    ]

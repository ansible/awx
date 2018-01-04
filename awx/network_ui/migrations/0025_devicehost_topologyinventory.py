# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0024_auto_20171213_1949'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceHost',
            fields=[
                ('device_host_id', models.AutoField(serialize=False, primary_key=True)),
                ('host_id', models.IntegerField()),
                ('device', models.ForeignKey(to='network_ui.Device')),
            ],
        ),
        migrations.CreateModel(
            name='TopologyInventory',
            fields=[
                ('topology_inventory_id', models.AutoField(serialize=False, primary_key=True)),
                ('inventory_id', models.IntegerField()),
                ('topology', models.ForeignKey(to='network_ui.Topology')),
            ],
        ),
    ]

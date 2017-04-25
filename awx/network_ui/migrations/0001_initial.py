# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('device_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('x', models.IntegerField()),
                ('y', models.IntegerField()),
                ('id', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('link_id', models.AutoField(serialize=False, primary_key=True)),
                ('from_device', models.ForeignKey(related_name='+', to='network_ui.Device')),
                ('to_device', models.ForeignKey(related_name='+', to='network_ui.Device')),
            ],
        ),
        migrations.CreateModel(
            name='Topology',
            fields=[
                ('topology_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('id', models.IntegerField()),
                ('scale', models.FloatField()),
                ('panX', models.FloatField()),
                ('panY', models.FloatField()),
            ],
        ),
        migrations.AddField(
            model_name='device',
            name='topology',
            field=models.ForeignKey(to='network_ui.Topology'),
        ),
    ]

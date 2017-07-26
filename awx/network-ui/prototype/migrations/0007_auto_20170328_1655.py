# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards_func(apps, schema_editor):
    Topology = apps.get_model("prototype", "Topology")
    Topology.objects.get_or_create(name="Unknown", topology_id=1, panX=0, panY=0, scale=1.0)
    Device = apps.get_model("prototype", "Device")
    Device.objects.get_or_create(name="Unknown", device_id=1, x=0, y=0, type="unknown", id=1, topology_id=1)
    Interface = apps.get_model("prototype", "Interface")
    Interface.objects.get_or_create(name="Unknown", device_id=1, interface_id=1)


class Migration(migrations.Migration):

    dependencies = [
        ('prototype', '0006_auto_20170321_1236'),
    ]

    operations = [
        migrations.CreateModel(
            name='Interface',
            fields=[
                ('interface_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('device', models.ForeignKey(to='prototype.Device')),
            ],
        ),
        migrations.RunPython(forwards_func),
        migrations.AddField(
            model_name='link',
            name='from_interface',
            field=models.ForeignKey(related_name='+', default=1, to='prototype.Interface'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='link',
            name='to_interface',
            field=models.ForeignKey(related_name='+', default=1, to='prototype.Interface'),
            preserve_default=False,
        ),
    ]

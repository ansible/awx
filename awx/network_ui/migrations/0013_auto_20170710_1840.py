# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0012_auto_20170706_1526'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('group_id', models.AutoField(serialize=False, primary_key=True)),
                ('id', models.IntegerField(verbose_name=b'Group')),
                ('name', models.CharField(max_length=200)),
                ('x1', models.IntegerField()),
                ('y1', models.IntegerField(verbose_name=b'Group')),
                ('x2', models.IntegerField(verbose_name=b'Group')),
                ('y2', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='GroupDevice',
            fields=[
                ('group_device_id', models.AutoField(serialize=False, primary_key=True)),
                ('device', models.ForeignKey(to='network_ui.Device')),
                ('group', models.ForeignKey(to='network_ui.GroupDevice')),
            ],
        ),
        migrations.AddField(
            model_name='topology',
            name='group_id_seq',
            field=models.IntegerField(default=0),
        ),
    ]

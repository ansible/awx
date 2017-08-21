# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0017_auto_20170717_1813'),
    ]

    operations = [
        migrations.CreateModel(
            name='Process',
            fields=[
                ('process_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('type', models.CharField(max_length=200)),
                ('id', models.IntegerField(default=0)),
                ('device', models.ForeignKey(to='network_ui.Device')),
            ],
        ),
        migrations.CreateModel(
            name='Stream',
            fields=[
                ('stream_id', models.AutoField(serialize=False, verbose_name=b'Stream', primary_key=True)),
                ('label', models.CharField(max_length=200, verbose_name=b'Stream')),
                ('id', models.IntegerField(default=0)),
                ('from_device', models.ForeignKey(related_name='from_stream', to='network_ui.Stream')),
                ('to_device', models.ForeignKey(related_name='to_stream', to='network_ui.Stream')),
            ],
        ),
        migrations.AddField(
            model_name='group',
            name='type',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='topology',
            name='stream_id_seq',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='topology',
            name='group_id_seq',
            field=models.IntegerField(default=0, verbose_name=b'Topology'),
        ),
    ]

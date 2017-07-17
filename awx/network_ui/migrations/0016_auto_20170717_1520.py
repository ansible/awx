# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0015_auto_20170710_1937'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataBinding',
            fields=[
                ('data_binding_id', models.AutoField(serialize=False, verbose_name=b'DataBinding', primary_key=True)),
                ('column', models.IntegerField()),
                ('row', models.IntegerField()),
                ('table', models.CharField(max_length=200)),
                ('primary_key_id', models.IntegerField()),
                ('field', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='DataSheet',
            fields=[
                ('data_sheet_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('topology', models.ForeignKey(to='network_ui.Topology')),
            ],
        ),
        migrations.CreateModel(
            name='DataType',
            fields=[
                ('data_type_id', models.AutoField(serialize=False, primary_key=True)),
                ('type_name', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='databinding',
            name='data_type',
            field=models.ForeignKey(to='network_ui.DataType'),
        ),
        migrations.AddField(
            model_name='databinding',
            name='sheet',
            field=models.ForeignKey(to='network_ui.DataSheet'),
        ),
    ]

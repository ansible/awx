# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0016_auto_20170717_1520'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasheet',
            name='client',
            field=models.ForeignKey(default=1, to='network_ui.Client'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='databinding',
            name='data_binding_id',
            field=models.AutoField(serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='group',
            name='id',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='group',
            name='x2',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='group',
            name='y1',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='topology',
            name='device_id_seq',
            field=models.IntegerField(default=0),
        ),
    ]

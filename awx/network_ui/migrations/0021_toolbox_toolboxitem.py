# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0020_device_process_id_seq'),
    ]

    operations = [
        migrations.CreateModel(
            name='Toolbox',
            fields=[
                ('toolbox_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ToolboxItem',
            fields=[
                ('toolbox_item_id', models.AutoField(serialize=False, primary_key=True)),
                ('data', models.TextField()),
                ('toolbox', models.ForeignKey(to='network_ui.Toolbox')),
            ],
        ),
    ]

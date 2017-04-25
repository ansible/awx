# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prototype', '0008_interface_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='link',
            name='from_device',
            field=models.ForeignKey(related_name='from_link', to='prototype.Device'),
        ),
        migrations.AlterField(
            model_name='link',
            name='from_interface',
            field=models.ForeignKey(related_name='from_link', to='prototype.Interface'),
        ),
        migrations.AlterField(
            model_name='link',
            name='to_device',
            field=models.ForeignKey(related_name='to_link', to='prototype.Device'),
        ),
        migrations.AlterField(
            model_name='link',
            name='to_interface',
            field=models.ForeignKey(related_name='to_link', to='prototype.Interface'),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_v300_create_labels'),
    ]

    operations = [
        migrations.AlterField(
            model_name='label',
            name='organization',
            field=models.ForeignKey(related_name='labels', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Organization', help_text='Organization this label belongs to.', null=True),
        ),
    ]

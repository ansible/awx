# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-02-14 00:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0061_v350_track_native_credentialtype_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobhostsummary',
            name='ignored',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='jobhostsummary',
            name='rescued',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
    ]

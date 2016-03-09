# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_v300_rbac_migrations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organization',
            name='admins',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='users',
        ),
        migrations.RemoveField(
            model_name='team',
            name='users',
        ),
    ]

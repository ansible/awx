# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_v300_rbac_migrations'),
    ]

    operations = [
        migrations.RenameField(
            'Organization',
            'admins',
            'deprecated_admins',
        ),
        migrations.RenameField(
            'Organization',
            'users',
            'deprecated_users',
        ),
        migrations.RenameField(
            'Team',
            'users',
            'deprecated_users',
        ),
    ]

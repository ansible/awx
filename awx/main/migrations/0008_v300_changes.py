# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from awx.main.migrations import _system_tracking as system_tracking
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_v300_rbac_migrations'),
    ]

    operations = [
        migrations.RunPython(system_tracking.migrate_facts),
    ]

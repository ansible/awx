# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from awx.main.migrations import ActivityStreamDisabledMigration
from awx.main.migrations import _rbac as rbac
from awx.main.migrations import _migration_utils as migration_utils


class Migration(ActivityStreamDisabledMigration):

    dependencies = [
        ('main', '0021_v330_declare_new_rbac_roles'),
    ]

    operations = [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(rbac.create_roles),
    ]

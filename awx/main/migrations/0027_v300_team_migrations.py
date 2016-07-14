# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from awx.main.migrations import _rbac as rbac
from awx.main.migrations import _team_cleanup as team_cleanup
from awx.main.migrations import _migration_utils as migration_utils
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0026_v300_credential_unique'),
    ]

    operations = [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(team_cleanup.migrate_team),
        migrations.RunPython(rbac.rebuild_role_hierarchy),
    ]

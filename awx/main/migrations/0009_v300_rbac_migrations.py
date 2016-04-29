# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from awx.main.migrations import _rbac as rbac
from awx.main.migrations import _migration_utils as migration_utils
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_v300_rbac_changes'),
    ]

    operations = [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(rbac.migrate_users),
        migrations.RunPython(rbac.create_roles),
        migrations.RunPython(rbac.migrate_organization),
        migrations.RunPython(rbac.migrate_team),
        migrations.RunPython(rbac.migrate_inventory),
        migrations.RunPython(rbac.migrate_projects),
        migrations.RunPython(rbac.migrate_credential),
        migrations.RunPython(rbac.rebuild_role_hierarchy),
    ]

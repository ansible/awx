# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from awx.main.migrations import _rbac as rbac
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_v300_rbac_changes'),
    ]

    operations = [
        migrations.RunPython(rbac.init_rbac_migration),
        migrations.RunPython(rbac.migrate_users),
        migrations.RunPython(rbac.migrate_organization),
        migrations.RunPython(rbac.migrate_team),
        migrations.RunPython(rbac.migrate_inventory),
        migrations.RunPython(rbac.migrate_projects),
        migrations.RunPython(rbac.migrate_credential),
    ]

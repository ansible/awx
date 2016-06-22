# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from awx.main.migrations import _rbac as rbac
from awx.main.migrations import _migration_utils as migration_utils
from django.db import migrations
import awx.main.fields

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0025_v300_update_rbac_parents'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='credential',
            unique_together=set([('organization', 'name', 'kind')]),
        ),
        migrations.AlterField(
            model_name='credential',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'singleton:system_auditor', b'use_role', b'owner_role', b'organization.auditor_role'], to='main.Role', null=b'True'),
        ),
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(rbac.rebuild_role_hierarchy),
    ]

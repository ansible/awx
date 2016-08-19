# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from awx.main.migrations import _rbac as rbac
from awx.main.migrations import _migration_utils as migration_utils
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0031_v302_migrate_survey_passwords'),
    ]

    operations = [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.AlterField(
            model_name='credential',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'singleton:system_administrator', b'organization.admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AlterField(
            model_name='credential',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.RunPython(rbac.rebuild_role_hierarchy),
    ]

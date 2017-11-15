# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from awx.main.migrations import ActivityStreamDisabledMigration
from awx.main.migrations import _reencrypt as reencrypt
from awx.main.migrations import _migration_utils as migration_utils


class Migration(ActivityStreamDisabledMigration):

    dependencies = [
        ('main', '0010_v322_add_ovirt4_tower_inventory'),
    ]

    operations = [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(reencrypt.encrypt_survey_passwords),
    ]

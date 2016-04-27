# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from awx.main.migrations import _ask_for_variables as ask_for_variables
from awx.main.migrations import _migration_utils as migration_utils
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_v300_prompting_changes'),
    ]

    operations = [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(ask_for_variables.migrate_credential),
    ]

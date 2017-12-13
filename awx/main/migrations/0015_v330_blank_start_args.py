# -*- coding: utf-8 -*-
# Python
from __future__ import unicode_literals

# Django
from django.db import migrations, models

# AWX
from awx.main.migrations import _migration_utils as migration_utils
from awx.main.migrations._reencrypt import blank_old_start_args


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_v330_saved_launchtime_configs'),
    ]

    operations = [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations, migrations.RunPython.noop),
        migrations.RunPython(blank_old_start_args, migrations.RunPython.noop),
    ]

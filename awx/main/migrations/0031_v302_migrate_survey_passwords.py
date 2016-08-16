# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from awx.main.migrations import _save_password_keys
from awx.main.migrations import _migration_utils as migration_utils
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0030_v302_job_survey_passwords'),
    ]

    operations = [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(_save_password_keys.migrate_survey_passwords),
    ]

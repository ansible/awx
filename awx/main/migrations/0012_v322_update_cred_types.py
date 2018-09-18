# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# AWX
from awx.main.migrations import _migration_utils as migration_utils
from awx.main.migrations import _credentialtypes as credentialtypes

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_v322_encrypt_survey_passwords'),
    ]

    operations = [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(credentialtypes.add_azure_cloud_environment_field),
    ]

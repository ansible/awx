# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from awx.main.migrations import _migration_utils as migration_utils


def update_dashed_host_variables(apps, schema_editor):
    Host = apps.get_model('main', 'Host')
    for host in Host.objects.filter(variables='---'):
        host.variables = ''
        host.save()

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0032_v302_credential_permissions_update'),
    ]

    operations = [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(update_dashed_host_variables),
    ]

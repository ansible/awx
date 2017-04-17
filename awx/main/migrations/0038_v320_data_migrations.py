# -*- coding: utf-8 -*-
# Python
from __future__ import unicode_literals

# Django
from django.db import migrations

# AWX
from awx.main.migrations import _inventory_source as invsrc
from awx.main.migrations import _migration_utils as migration_utils


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0037_v320_release'),
    ]

    operations = [
        # Inventory Refresh
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(invsrc.remove_inventory_source_with_no_inventory_link),
        migrations.RunPython(invsrc.rename_inventory_sources),
    ]

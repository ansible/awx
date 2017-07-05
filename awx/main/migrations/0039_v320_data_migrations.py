# -*- coding: utf-8 -*-
# Python
from __future__ import unicode_literals

# Django
from django.db import migrations

# AWX
from awx.main.migrations import _inventory_source as invsrc
from awx.main.migrations import _migration_utils as migration_utils
from awx.main.migrations import _reencrypt
from awx.main.migrations import _scan_jobs


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0038_v320_release'),
    ]

    operations = [
        # Inventory Refresh
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(invsrc.remove_rax_inventory_sources),
        migrations.RunPython(invsrc.remove_inventory_source_with_no_inventory_link),
        migrations.RunPython(invsrc.rename_inventory_sources),
        migrations.RunPython(_reencrypt.replace_aesecb_fernet),
        migrations.RunPython(_scan_jobs.migrate_scan_job_templates),
    ]

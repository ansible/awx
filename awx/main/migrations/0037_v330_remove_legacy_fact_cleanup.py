# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# AWX
from awx.main.migrations._scan_jobs import remove_legacy_fact_cleanup

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0036_v330_credtype_remove_become_methods'),
    ]

    operations = [
        migrations.RunPython(remove_legacy_fact_cleanup),
    ]

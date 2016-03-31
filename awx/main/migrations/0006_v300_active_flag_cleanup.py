# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from awx.main.migrations import _cleanup_deleted as cleanup_deleted
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_v300_migrate_facts'),
    ]

    operations = [
        migrations.RunPython(cleanup_deleted.cleanup_deleted),
    ]

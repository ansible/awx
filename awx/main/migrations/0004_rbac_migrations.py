# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from awx.main.migrations import _rbac as rbac
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_rbac_changes'),
    ]

    operations = [
        migrations.RunPython(rbac.migrate_organization),
        migrations.RunPython(rbac.migrate_credential),
    ]

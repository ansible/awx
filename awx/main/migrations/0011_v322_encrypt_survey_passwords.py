# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from awx.main.migrations import ActivityStreamDisabledMigration
from awx.main.migrations import _reencrypt as reencrypt


class Migration(ActivityStreamDisabledMigration):

    dependencies = [
        ('main', '0010_v322_add_support_for_ovirt4_inventory'),
    ]

    operations = [
        migrations.RunPython(reencrypt.encrypt_survey_passwords),
    ]

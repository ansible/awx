# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from awx.main.migrations import _rbac as rbac
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_v300_changes'),
    ]

    operations = [
        # This is a placeholder for our future active flag removal work
    ]

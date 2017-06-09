# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from awx.main.migrations import _reencrypt


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0043_v320_instancegroups'),
    ]

    operations = [
        migrations.RunPython(_reencrypt.replace_aesecb_fernet),
    ]

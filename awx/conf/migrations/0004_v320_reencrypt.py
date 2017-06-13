# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from awx.conf.migrations import _reencrypt


class Migration(migrations.Migration):

    dependencies = [
        ('conf', '0003_v310_JSONField_changes'),
    ]

    operations = [
        migrations.RunPython(_reencrypt.replace_aesecb_fernet),
    ]

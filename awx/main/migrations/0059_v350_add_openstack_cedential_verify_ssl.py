# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# AWX
from awx.main.migrations import _credentialtypes as credentialtypes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0058_v350_remove_limit_limit'),
    ]

    operations = [
        migrations.RunPython(credentialtypes.add_openstack_verify_field),
    ]

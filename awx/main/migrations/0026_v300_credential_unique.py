# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0025_v300_update_rbac_parents'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='credential',
            unique_together=set([('organization', 'name', 'kind')]),
        ),
    ]

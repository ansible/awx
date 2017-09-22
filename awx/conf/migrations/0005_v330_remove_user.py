# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import migrations


def remove_user_defined_configurations(apps, schema_editor):
    Setting = apps.get_model('conf', 'Setting')
    for setting_to_del in Setting.objects.filter(user__isnull=False):
        setting_to_del.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('conf', '0004_v320_reencrypt'),
    ]

    operations = [
        migrations.RunPython(
            remove_user_defined_configurations
        ),
        migrations.RemoveField(
            model_name='setting',
            name='user',
        ),
    ]

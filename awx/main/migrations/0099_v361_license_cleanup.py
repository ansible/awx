# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def _cleanup_license_setting(apps, schema_editor):
    Setting = apps.get_model('conf', 'Setting')
    for license in Setting.objects.filter(key='LICENSE').all():
        for k in ('rh_username', 'rh_password'):
            license.value.pop(k, None)
        license.save()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0098_v360_rename_cyberark_aim_credential_type'),
    ]

    operations = [migrations.RunPython(_cleanup_license_setting)]

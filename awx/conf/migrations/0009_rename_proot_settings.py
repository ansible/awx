# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations
from awx.conf.migrations import _rename_setting


def rename_proot_settings(apps, schema_editor):
    _rename_setting.rename_setting(apps, schema_editor, old_key='AWX_PROOT_BASE_PATH', new_key='AWX_ISOLATION_BASE_PATH')
    _rename_setting.rename_setting(apps, schema_editor, old_key='AWX_PROOT_SHOW_PATHS', new_key='AWX_ISOLATION_SHOW_PATHS')


class Migration(migrations.Migration):
    dependencies = [('conf', '0008_subscriptions')]

    operations = [migrations.RunPython(rename_proot_settings)]

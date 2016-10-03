# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from django.db import migrations


def copy_tower_settings(apps, schema_editor):
    TowerSettings = apps.get_model('main', 'TowerSettings')
    Setting = apps.get_model('conf', 'Setting')
    for tower_setting in TowerSettings.objects.all().iterator():
        try:
            value = tower_setting.value
            # LICENSE is stored as a string; convert it to a dict.
            if tower_setting.key == 'LICENSE':
                value = json.loads(value)
            # Anything else (e.g. TOWER_URL_BASE) that is stored as a string
            # needs to be converted to a JSON-encoded string to work with the
            # JSON field.
            elif tower_setting.value_type == 'string':
                value = json.dumps(value)
            setting, created = Setting.objects.get_or_create(
                key=tower_setting.key,
                user=tower_setting.user,
                defaults=dict(value=value),
            )
            if not created and setting.value != value:
                setting.value = value
                setting.save(update_fields=['value'])
        except Setting.MultipleObjectsReturned:
            pass


def revert_tower_settings(apps, schema_editor):
    TowerSettings = apps.get_model('main', 'TowerSettings')
    Setting = apps.get_model('conf', 'Setting')
    for setting in Setting.objects.all().iterator():
        value = setting.value
        # LICENSE is stored as a JSON object; convert it back to a string.
        if setting.key == 'LICENSE':
            value = json.dumps(value)
        defaults = dict(
            value=value,
            value_type='string',
            description='',
            category='',
        )
        try:
            tower_setting, created = TowerSettings.objects.get_or_create(
                key=setting.key,
                user=setting.user,
                defaults=defaults,
            )
            if not created:
                update_fields = []
                for k, v in defaults.items():
                    if getattr(tower_setting, k) != v:
                        setattr(tower_setting, k, v)
                        update_fields.append(k)
                if update_fields:
                    tower_setting.save(update_fields=update_fields)
        except TowerSettings.MultipleObjectsReturned:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('conf', '0001_initial'),
        ('main', '0035_v310_jobevent_uuid'),
    ]

    run_before = [
        ('main', '0036_v310_remove_tower_settings'),
    ]

    operations = [
        migrations.RunPython(copy_tower_settings, revert_tower_settings),
    ]

# Copyright (c) 2015 Ansible, Inc..
# All Rights Reserved.

import json
from django.conf import settings as django_settings
from awx.main.models.configuration import TowerSettings

class TowerConfiguration(object):

    def __getattr__(self, key):
        ts = TowerSettings.objects.filter(key=key)
        if not ts.exists():
            return getattr(django_settings, key)
        return ts[0].value_converted

    def create(key, value):
        settings_manifest = django_settings.TOWER_SETTINGS_MANIFEST
        if key not in settings_manifest:
            raise AttributeError("Tower Setting with key '{0}' does not exist".format(key))
        settings_entry = settings_manifest[key]
        setting_actual = TowerSettings.objects.filter(key=key)
        if not settings_actual.exists():
            settings_actual = TowerSettings(key=key,
                                            description=settings_entry['description'],
                                            category=settings_entry['category'],
                                            value=value,
                                            value_type=settings_entry['type'])
        else:
            settings_actual['value'] = value
        settings_actual.save()

tower_settings = TowerConfiguration()

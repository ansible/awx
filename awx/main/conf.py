# Copyright (c) 2015 Ansible, Inc..
# All Rights Reserved.

import json
from django.conf import settings as django_settings
from awx.main.models.configuration import TowerSettings

class TowerConfiguration(object):

    # TODO: Caching so we don't have to hit the database every time for settings
    def __getattr__(self, key):
        settings_manifest = django_settings.TOWER_SETTINGS_MANIFEST
        if key not in settings_manifest:
            raise AttributeError("Tower Setting with key '{0}' is not defined in the manifest".format(key))
        ts = TowerSettings.objects.filter(key=key)
        if not ts.exists():
            try:
                val_actual = getattr(django_settings, key)
            except AttributeError:
                val_actual = settings_manifest[key]['default']
            return val_actual
        return ts[0].value_converted

    def __setattr__(self, key, value):
        settings_manifest = django_settings.TOWER_SETTINGS_MANIFEST
        if key not in settings_manifest:
            raise AttributeError("Tower Setting with key '{0}' does not exist".format(key))
        settings_entry = settings_manifest[key]
        settings_actual = TowerSettings.objects.filter(key=key)
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

# Copyright (c) 2015 Ansible, Inc..
# All Rights Reserved.

import logging

from django.conf import settings as django_settings
from django.db.utils import ProgrammingError
from django.db import OperationalError
from awx.main.models.configuration import TowerSettings

logger = logging.getLogger('awx.main.conf')

class TowerConfiguration(object):

    # TODO: Caching so we don't have to hit the database every time for settings
    def __getattr__(self, key):
        settings_manifest = django_settings.TOWER_SETTINGS_MANIFEST
        if key not in settings_manifest:
            raise AttributeError("Tower Setting with key '{0}' is not defined in the manifest".format(key))
        default_value = settings_manifest[key]['default']
        ts = TowerSettings.objects.filter(key=key)
        try:
            if not ts.exists():
                try:
                    val_actual = getattr(django_settings, key)
                except AttributeError:
                    val_actual = default_value
                return val_actual
            return ts[0].value_converted
        except (ProgrammingError, OperationalError), e:
            # Database is not available yet, usually during migrations so lets use the default
            logger.debug("Database settings not available yet, using defaults ({0})".format(e))
            return default_value

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
            settings_actual = settings_actual[0]
            settings_actual.value = value
        settings_actual.save()

tower_settings = TowerConfiguration()

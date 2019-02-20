#!/usr/bin/env python

# AWX
from awx.conf.registry import settings_registry

__all__ = ['conf_to_dict']


def conf_to_dict(obj):
    return {
        'category': settings_registry.get_setting_category(obj.key),
        'name': obj.key,
    }

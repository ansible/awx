# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.utils.module_loading import autodiscover_modules

# AWX
from .registry import settings_registry


def register(setting, **kwargs):
    settings_registry.register(setting, **kwargs)


def register_validate(category, func):
    settings_registry.register_validate(category, func)


def autodiscover():
    autodiscover_modules('conf', register_to=settings_registry)

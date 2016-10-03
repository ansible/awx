# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.core.cache import cache
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework.exceptions import APIException

# Tower
from awx.main.task_engine import TaskEnhancer
from awx.main.utils import memoize

__all__ = ['LicenseForbids', 'get_license', 'feature_enabled', 'feature_exists']


class LicenseForbids(APIException):
    status_code = 402
    default_detail = _('Your Tower license does not allow that.')


@memoize(cache_key='_validated_license_data')
def _get_validated_license_data():
    return TaskEnhancer().validate_enhancements()


@receiver(setting_changed)
def _on_setting_changed(sender, **kwargs):
    # Clear cached result above when license changes.
    if kwargs.get('setting', None) == 'LICENSE':
        cache.delete('_validated_license_data')


def get_license(show_key=False):
    """Return a dictionary representing the active license on this Tower instance."""
    license_data = _get_validated_license_data()
    if not show_key:
        license_data.pop('license_key', None)
    return license_data


def feature_enabled(name):
    """Return True if the requested feature is enabled, False otherwise."""
    return _get_validated_license_data().get('features', {}).get(name, False)


def feature_exists(name):
    """Return True if the requested feature name exists, False otherwise."""
    return bool(name in _get_validated_license_data().get('features', {}))

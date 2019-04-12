# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Tower
from awx.main.utils.common import get_licenser

__all__ = ['get_license']


def _get_validated_license_data():
    return get_licenser().validate()


def get_license(show_key=False):
    """Return a dictionary representing the active license on this Tower instance."""
    license_data = _get_validated_license_data()
    if not show_key:
        license_data.pop('license_key', None)
    return license_data

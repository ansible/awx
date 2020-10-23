# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

__all__ = ['get_license']


def _get_validated_license_data():
    from awx.main.utils import get_licenser
    return get_licenser().validate()


def get_license():
    """Return a dictionary representing the active license on this Tower instance."""
    return _get_validated_license_data()

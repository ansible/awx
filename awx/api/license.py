# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from rest_framework.exceptions import APIException

from awx.main.task_engine import TaskSerializer
from awx.main.utils import memoize


class LicenseForbids(APIException):
    status_code = 402
    default_detail = 'Your Tower license does not allow that.'


@memoize()
def get_license(show_key=False, bypass_database=False):
    """Return a dictionary representing the license currently in
    place on this Tower instance.
    """
    license_reader = TaskSerializer()
    if bypass_database:
        return license_reader.from_file(show_key=show_key)
    return license_reader.from_database(show_key=show_key)


def feature_enabled(name, bypass_database=False):
    """Return True if the requested feature is enabled, False otherwise.
    If the feature does not exist, raise KeyError.
    """
    license = get_license(bypass_database=bypass_database)

    # Sanity check: If there is no license, the feature is considered
    # to be off.
    if 'features' not in license:
        return False

    # Return the correct feature flag.
    return license['features'].get(name, False)

def feature_exists(name):
    """Return True if the requested feature is enabled, False otherwise.
    If the feature does not exist, raise KeyError.
    """
    license = get_license()

    # Sanity check: If there is no license, the feature is considered
    # to be off.
    if 'features' not in license:
        return False

    return name in license['features']

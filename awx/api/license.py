# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from rest_framework.exceptions import APIException

from awx.main.task_engine import TaskSerializer


class LicenseForbids(APIException):
    status_code = 402
    default_detail = 'Your Tower license does not allow that.'


def get_license(show_key=False):
    """Return a dictionary representing the license currently in
    place on this Tower instance.
    """
    license_reader = TaskSerializer()
    return license_reader.from_file(show_key=show_key)


def feature_enabled(name):
    """Return True if the requested feature is enabled, False otherwise.
    If the feature does not exist, raise KeyError.
    """
    return get_license()['features'][name]

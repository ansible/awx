# Copyright (c) 2016 Ansible, Inc.

# Python
from unittest import mock

# AWX
from awx.main.ha import is_ha_environment


@mock.patch('awx.main.models.Instance.objects.count', lambda: 2)
def test_multiple_instances():
    assert is_ha_environment()


@mock.patch('awx.main.models.Instance.objects.count', lambda: 1)
def test_db_localhost():
    assert is_ha_environment() is False

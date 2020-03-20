from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.conf.models import Setting


@pytest.mark.django_db
def test_setting_flat_value(run_module, admin_user):
    the_value = 'CN=service_account,OU=ServiceAccounts,DC=domain,DC=company,DC=org'
    result = run_module('tower_settings', dict(
        name='AUTH_LDAP_BIND_DN',
        value=the_value
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    assert Setting.objects.get(key='AUTH_LDAP_BIND_DN').value == the_value


@pytest.mark.django_db
def test_setting_dict_value(run_module, admin_user):
    the_value = {
        'email': 'mail',
        'first_name': 'givenName',
        'last_name': 'surname'
    }
    result = run_module('tower_settings', dict(
        name='AUTH_LDAP_USER_ATTR_MAP',
        value=the_value
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    assert Setting.objects.get(key='AUTH_LDAP_USER_ATTR_MAP').value == the_value


@pytest.mark.django_db
def test_setting_nested_type(run_module, admin_user):
    the_value = {
        'email': 'mail',
        'first_name': 'givenName',
        'last_name': 'surname'
    }
    result = run_module('tower_settings', dict(
        settings={
            'AUTH_LDAP_USER_ATTR_MAP': the_value
        }
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    assert Setting.objects.get(key='AUTH_LDAP_USER_ATTR_MAP').value == the_value


@pytest.mark.django_db
def test_setting_bool_value(run_module, admin_user):
    for the_value in (True, False):
        result = run_module('tower_settings', dict(
            name='ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC',
            value=the_value
        ), admin_user)
        assert not result.get('failed', False), result.get('msg', result)
        assert result.get('changed'), result

        assert Setting.objects.get(key='ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC').value is the_value

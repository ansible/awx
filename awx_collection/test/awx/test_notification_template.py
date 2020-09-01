from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import NotificationTemplate


def compare_with_encrypted(model_config, param_config):
    '''Given a model_config from the database, assure that this is consistent
    with the config given in the notification_configuration parameter
    this requires handling of password fields
    '''
    for key, model_val in model_config.items():
        param_val = param_config.get(key, 'missing')
        if isinstance(model_val, str) and (model_val.startswith('$encrypted$') or param_val.startswith('$encrypted$')):
            assert model_val.startswith('$encrypted$')  # must be saved as encrypted
            assert len(model_val) > len('$encrypted$')
        else:
            assert model_val == param_val, 'Config key {0} did not match, (model: {1}, input: {2})'.format(
                key, model_val, param_val
            )


@pytest.mark.django_db
def test_create_modify_notification_template(run_module, admin_user, organization):
    nt_config = {
        'username': 'user',
        'password': 'password',
        'sender': 'foo@invalid.com',
        'recipients': ['foo2@invalid.com'],
        'host': 'smtp.example.com',
        'port': 25,
        'use_tls': False, 'use_ssl': False,
        'timeout': 4
    }
    result = run_module('tower_notification_template', dict(
        name='foo-notification-template',
        organization=organization.name,
        notification_type='email',
        notification_configuration=nt_config,
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.pop('changed', None), result

    nt = NotificationTemplate.objects.get(id=result['id'])
    compare_with_encrypted(nt.notification_configuration, nt_config)
    assert nt.organization == organization

    # Test no-op, this is impossible if the notification_configuration is given
    # because we cannot determine if password fields changed
    result = run_module('tower_notification_template', dict(
        name='foo-notification-template',
        organization=organization.name,
        notification_type='email',
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert not result.pop('changed', None), result

    # Test a change in the configuration
    nt_config['timeout'] = 12
    result = run_module('tower_notification_template', dict(
        name='foo-notification-template',
        organization=organization.name,
        notification_type='email',
        notification_configuration=nt_config,
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.pop('changed', None), result

    nt.refresh_from_db()
    compare_with_encrypted(nt.notification_configuration, nt_config)


@pytest.mark.django_db
def test_invalid_notification_configuration(run_module, admin_user, organization):
    result = run_module('tower_notification_template', dict(
        name='foo-notification-template',
        organization=organization.name,
        notification_type='email',
        notification_configuration={},
    ), admin_user)
    assert result.get('failed', False), result.get('msg', result)
    assert 'Missing required fields for Notification Configuration' in result['msg']


@pytest.mark.django_db
def test_deprecated_to_modern_no_op(run_module, admin_user, organization):
    nt_config = {
        'url': 'http://www.example.com/hook',
        'headers': {
            'X-Custom-Header': 'value123'
        }
    }
    result = run_module('tower_notification_template', dict(
        name='foo-notification-template',
        organization=organization.name,
        notification_type='webhook',
        notification_configuration=nt_config,
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.pop('changed', None), result

    result = run_module('tower_notification_template', dict(
        name='foo-notification-template',
        organization=organization.name,
        notification_type='webhook',
        notification_configuration=nt_config,
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert not result.pop('changed', None), result

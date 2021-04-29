from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from unittest import mock

from awx.main.models import User


@pytest.fixture
def mock_auth_stuff():
    """Some really specific session-related stuff is done for changing or setting
    passwords, so we will just avoid that here.
    """
    with mock.patch('awx.api.serializers.update_session_auth_hash'):
        yield


@pytest.mark.django_db
def test_create_user(run_module, admin_user, mock_auth_stuff):
    result = run_module('user', dict(username='Bob', password='pass4word'), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    user = User.objects.get(id=result['id'])
    assert user.username == 'Bob'


@pytest.mark.django_db
def test_password_no_op_warning(run_module, admin_user, mock_auth_stuff, silence_warning):
    for i in range(2):
        result = run_module('user', dict(username='Bob', password='pass4word'), admin_user)
        assert not result.get('failed', False), result.get('msg', result)

    assert result.get('changed')  # not actually desired, but assert for sanity

    silence_warning.assert_called_once_with(
        "The field password of user {0} has encrypted data and " "may inaccurately report task is changed.".format(result['id'])
    )


@pytest.mark.django_db
def test_update_password_on_create(run_module, admin_user, mock_auth_stuff):
    for i in range(2):
        result = run_module('user', dict(username='Bob', password='pass4word', update_secrets=False), admin_user)
        assert not result.get('failed', False), result.get('msg', result)

    assert not result.get('changed')


@pytest.mark.django_db
def test_update_user(run_module, admin_user, mock_auth_stuff):
    result = run_module('user', dict(username='Bob', password='pass4word', is_system_auditor=True), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    update_result = run_module('user', dict(username='Bob', is_system_auditor=False), admin_user)

    assert update_result.get('changed')
    user = User.objects.get(id=result['id'])
    assert not user.is_system_auditor

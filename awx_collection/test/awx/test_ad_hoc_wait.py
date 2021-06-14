from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from django.utils.timezone import now

from awx.main.models.ad_hoc_commands import AdHocCommand


@pytest.mark.django_db
def test_ad_hoc_command_wait_successful(run_module, admin_user):
    command = AdHocCommand.objects.create(status='successful', started=now(), finished=now())
    result = run_module('ad_hoc_command_wait', dict(command_id=command.id), admin_user)
    result.pop('invocation', None)
    result['elapsed'] = float(result['elapsed'])
    assert result.pop('finished', '')[:10] == str(command.finished)[:10]
    assert result.pop('started', '')[:10] == str(command.started)[:10]
    assert result.pop('status', "successful"), result
    assert result.get('changed') is False


@pytest.mark.django_db
def test_ad_hoc_command_wait_failed(run_module, admin_user):
    command = AdHocCommand.objects.create(status='failed', started=now(), finished=now())
    result = run_module('ad_hoc_command_wait', dict(command_id=command.id), admin_user)
    result.pop('invocation', None)
    result['elapsed'] = float(result['elapsed'])
    assert result.pop('finished', '')[:10] == str(command.finished)[:10]
    assert result.pop('started', '')[:10] == str(command.started)[:10]
    assert result.get('changed') is False
    assert result.pop('status', "failed"), result


@pytest.mark.django_db
def test_ad_hoc_command_wait_not_found(run_module, admin_user):
    result = run_module('ad_hoc_command_wait', dict(command_id=42), admin_user)
    result.pop('invocation', None)
    assert result == {"failed": True, "msg": "Unable to wait on ad hoc command 42; that ID does not exist."}

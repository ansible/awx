from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from django.utils.timezone import now

from awx.main.models.ad_hoc_commands import AdHocCommand


@pytest.mark.django_db
def test_ad_hoc_command_wait_successful(run_module, admin_user):
    command = AdHocCommand.objects.create(status='successful', started=now(), finished=now())
    result = run_module('tower_ad_hoc_command_wait', dict(
        command_id=command.id
    ), admin_user)
    result.pop('invocation', None)
    assert result.pop('finished', '')[:10] == str(command.finished)[:10]
    assert result.pop('started', '')[:10] == str(command.started)[:10]
    assert result == {
        "status": "successful",
        "changed": False,
        "elapsed": str(command.elapsed),
        "id": command.id
    }


@pytest.mark.django_db
def test_ad_hoc_command_wait_failed(run_module, admin_user):
    command = AdHocCommand.objects.create(status='failed', started=now(), finished=now())
    result = run_module('tower_ad_hoc_command_wait', dict(
        command_id=command.id
    ), admin_user)
    result.pop('invocation', None)
    assert result.pop('finished', '')[:10] == str(command.finished)[:10]
    assert result.pop('started', '')[:10] == str(command.started)[:10]
    assert result == {
        "status": "failed",
        "failed": True,
        "changed": False,
        "elapsed": str(command.elapsed),
        "id": command.id,
        "msg": "The ad hoc command - 1, failed"
    }


@pytest.mark.django_db
def test_ad_hoc_command_wait_not_found(run_module, admin_user):
    result = run_module('tower_ad_hoc_command_wait', dict(
        command_id=42
    ), admin_user)
    result.pop('invocation', None)
    assert result == {
        "failed": True,
        "msg": "Unable to wait on ad hoc command 42; that ID does not exist in Tower."
    }

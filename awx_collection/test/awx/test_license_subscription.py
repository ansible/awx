from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest


@pytest.mark.django_db
def test_license_invalid_subscription_id_should_fail(run_module, admin_user):
    """Test invalid subscription ID returns failure."""
    result = run_module('license', {'subscription_id': 'invalid-test-12345', 'state': 'present'}, admin_user)

    assert result.get('failed', False)
    assert 'msg' in result
    assert 'subscription' in result['msg'].lower()


@pytest.mark.django_db
def test_license_invalid_manifest_should_fail(run_module, admin_user):
    """Test invalid manifest returns failure."""
    result = run_module('license', {'manifest': '/nonexistent/test.zip', 'state': 'present'}, admin_user)

    assert result.get('failed', False)
    assert 'msg' in result


@pytest.mark.django_db
def test_license_state_absent_works(run_module, admin_user):
    """Test license removal works."""
    result = run_module('license', {'state': 'absent'}, admin_user)

    assert not result.get('failed', False)

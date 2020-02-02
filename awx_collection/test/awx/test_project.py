from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import Project


@pytest.mark.django_db
def test_create_project(run_module, admin_user, organization):
    result = run_module('tower_project', dict(
        name='foo',
        organization=organization.name,
        scm_type='git',
        scm_url='https://foo.invalid',
        wait=False
    ), admin_user)
    warning = ['scm_update_cache_timeout will be ignored since scm_update_on_launch was not set to true']
    assert result.pop('changed', None), result

    proj = Project.objects.get(name='foo')
    assert proj.scm_url == 'https://foo.invalid'
    assert proj.organization == organization

    result.pop('invocation')
    result.pop('existing_credential_type')
    assert result == {
        'credential_type': 'Nexus',
        'state': 'present',
        'name': 'foo',
        'id': proj.id,
        'warnings': warning
    }

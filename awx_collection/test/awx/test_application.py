from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models import Organization
from awx.main.models.oauth import OAuth2Application


@pytest.mark.django_db
def test_create_application(run_module, admin_user):
    org = Organization.objects.create(name='foo')

    module_args = {
        'name': 'foo_app',
        'description': 'barfoo',
        'state': 'present',
        'authorization_grant_type': 'password',
        'client_type': 'public',
        'organization': 'foo',
    }

    result = run_module('application', module_args, admin_user)
    assert result.get('changed'), result

    application = OAuth2Application.objects.get(name='foo_app')
    assert application.description == 'barfoo'
    assert application.organization_id == org.id

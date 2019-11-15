from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import Organization, Team


@pytest.mark.django_db
def test_create_team(run_module, admin_user):
    org = Organization.objects.create(name='foo')

    result = run_module('tower_organization', {
        'name': 'foo_team',
        'description': 'fooin around',
        'state': 'present',
        'organization': 'foo'
    }, admin_user)

    team = Team.objects.filter(name='foo_team').first()

    result.pop('invocation')
    assert result == {
        "team": "foo_team",
        "state": "present",
        "id": team.id if team else None,
        "changed": True
    }

    team = Team.objects.get(name='foo_team')
    assert team.description == 'fooin around'
    assert team.organization_id == org.id

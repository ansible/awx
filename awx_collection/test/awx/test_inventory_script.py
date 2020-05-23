from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import Organization, InventoryScript


@pytest.mark.django_db
def test_create_project(run_module, admin_user, organization, silence_warning):
    result = run_module('tower_inventory_script', dict(
        name='foo',
        organization=organization.name,
        description='this is the description',
        script='#!/usr/bin/env python test',
    ), admin_user)

    assert result.pop('changed', None), result

    inv_s = InventoryScript.objects.get(name='foo')
    assert inv_s.organization == organization
    assert inv_src.description == 'this is the description'
    assert inv_src.script == '#!/usr/bin/env python test'


    result.pop('invocation')
    assert result == {
        'name': 'foo',
        'id': inv_s.id
    }

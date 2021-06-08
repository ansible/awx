from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models import Organization, Inventory, Group, Host


@pytest.mark.django_db
def test_create_group(run_module, admin_user):
    org = Organization.objects.create(name='test-org')
    inv = Inventory.objects.create(name='test-inv', organization=org)
    variables = {"ansible_network_os": "iosxr"}

    result = run_module('group', dict(name='Test Group', inventory='test-inv', variables=variables, state='present'), admin_user)
    assert result.get('changed'), result

    group = Group.objects.get(name='Test Group')
    assert group.inventory == inv
    assert group.variables == '{"ansible_network_os": "iosxr"}'

    result.pop('invocation')
    assert result == {
        'id': group.id,
        'name': 'Test Group',
        'changed': True,
    }


@pytest.mark.django_db
def test_associate_hosts_and_children(run_module, admin_user, organization):
    inv = Inventory.objects.create(name='test-inv', organization=organization)
    group = Group.objects.create(name='Test Group', inventory=inv)

    inv_hosts = [Host.objects.create(inventory=inv, name='foo{0}'.format(i)) for i in range(3)]
    group.hosts.add(inv_hosts[0], inv_hosts[1])

    child = Group.objects.create(inventory=inv, name='child_group')

    result = run_module(
        'group',
        dict(name='Test Group', inventory='test-inv', hosts=[inv_hosts[1].name, inv_hosts[2].name], children=[child.name], state='present'),
        admin_user,
    )
    assert not result.get('failed', False), result.get('msg', result)
    assert result['changed'] is True

    assert set(group.hosts.all()) == set([inv_hosts[1], inv_hosts[2]])
    assert set(group.children.all()) == set([child])


@pytest.mark.django_db
def test_associate_on_create(run_module, admin_user, organization):
    inv = Inventory.objects.create(name='test-inv', organization=organization)
    child = Group.objects.create(name='test-child', inventory=inv)
    host = Host.objects.create(name='test-host', inventory=inv)

    result = run_module('group', dict(name='Test Group', inventory='test-inv', hosts=[host.name], groups=[child.name], state='present'), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result['changed'] is True

    group = Group.objects.get(pk=result['id'])
    assert set(group.hosts.all()) == set([host])
    assert set(group.children.all()) == set([child])


@pytest.mark.django_db
def test_children_alias_of_groups(run_module, admin_user, organization):
    inv = Inventory.objects.create(name='test-inv', organization=organization)
    group = Group.objects.create(name='Test Group', inventory=inv)
    child = Group.objects.create(inventory=inv, name='child_group')
    result = run_module('group', dict(name='Test Group', inventory='test-inv', groups=[child.name], state='present'), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result['changed'] is True

    assert set(group.children.all()) == set([child])


@pytest.mark.django_db
def test_group_idempotent(run_module, admin_user):
    # https://github.com/ansible/ansible/issues/46803
    org = Organization.objects.create(name='test-org')
    inv = Inventory.objects.create(name='test-inv', organization=org)
    group = Group.objects.create(
        name='Test Group',
        inventory=inv,
    )

    result = run_module('group', dict(name='Test Group', inventory='test-inv', state='present'), admin_user)

    result.pop('invocation')
    assert result == {
        'id': group.id,
        'changed': False,  # idempotency assertion
    }

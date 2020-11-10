import pytest
from unittest import mock

from awx.main.migrations import _inventory_source as invsrc

from django.apps import apps

from awx.main.models import InventorySource, InventoryUpdate, ManagedCredentialType, CredentialType, Credential


@pytest.mark.parametrize('vars,id_var,result', [
    ({'foo': {'bar': '1234'}}, 'foo.bar', '1234'),
    ({'cat': 'meow'}, 'cat', 'meow'),
    ({'dog': 'woof'}, 'cat', '')
])
def test_instance_id(vars, id_var, result):
    assert invsrc._get_instance_id(vars, id_var) == result


@pytest.mark.django_db
def test_apply_new_instance_id(inventory_source):
    host1 = inventory_source.hosts.create(
        name='foo1', inventory=inventory_source.inventory,
        variables={'foo': 'bar'}, instance_id=''
    )
    host2 = inventory_source.hosts.create(
        name='foo2', inventory=inventory_source.inventory,
        variables={'foo': 'bar'}, instance_id='bad_user'
    )
    with mock.patch('django.conf.settings.{}_INSTANCE_ID_VAR'.format(inventory_source.source.upper()), 'foo'):
        invsrc.set_new_instance_id(apps, inventory_source.source, 'foo')
    host1.refresh_from_db()
    host2.refresh_from_db()
    assert host1.instance_id == 'bar'
    assert host2.instance_id == 'bad_user'
    with mock.patch('django.conf.settings.{}_INSTANCE_ID_VAR'.format(inventory_source.source.upper()), 'foo'):
        invsrc.back_out_new_instance_id(apps, inventory_source.source, 'foo')
    host1.refresh_from_db()
    host2.refresh_from_db()
    assert host1.instance_id == ''
    assert host2.instance_id == 'bad_user'


@pytest.mark.django_db
def test_cloudforms_inventory_removal(inventory):
    ManagedCredentialType(
        name='Red Hat CloudForms',
        namespace='cloudforms',
        kind='cloud',
        managed_by_tower=True,
        inputs={},
    )
    CredentialType.defaults['cloudforms']().save()
    cloudforms = CredentialType.objects.get(namespace='cloudforms')
    Credential.objects.create(
        name='test',
        credential_type=cloudforms,
    )

    for source in ('ec2', 'cloudforms'):
        i = InventorySource.objects.create(
            name='test',
            inventory=inventory,
            organization=inventory.organization,
            source=source,
        )
        InventoryUpdate.objects.create(
            name='test update',
            inventory_source=i,
            source=source,
        )
    assert Credential.objects.count() == 1
    assert InventorySource.objects.count() == 2  # ec2 + cf
    assert InventoryUpdate.objects.count() == 2  # ec2 + cf
    invsrc.delete_cloudforms_inv_source(apps, None)
    assert InventorySource.objects.count() == 1  # ec2
    assert InventoryUpdate.objects.count() == 1  # ec2
    assert InventorySource.objects.first().source == 'ec2'
    assert InventoryUpdate.objects.first().source == 'ec2'
    assert Credential.objects.count() == 0
    assert CredentialType.objects.filter(namespace='cloudforms').exists() is False

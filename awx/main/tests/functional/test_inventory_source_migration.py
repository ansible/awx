import pytest
from unittest import mock

from awx.main.migrations import _inventory_source as invsrc
from awx.main.models import InventorySource

from django.apps import apps


@pytest.mark.django_db
def test_inv_src_manual_removal(inventory_source):
    inventory_source.source = ''
    inventory_source.save()

    assert InventorySource.objects.filter(pk=inventory_source.pk).exists()
    invsrc.remove_manual_inventory_sources(apps, None)
    assert not InventorySource.objects.filter(pk=inventory_source.pk).exists()


@pytest.mark.django_db
def test_rax_inv_src_removal(inventory_source):
    inventory_source.source = 'rax'
    inventory_source.save()

    assert InventorySource.objects.filter(pk=inventory_source.pk).exists()
    invsrc.remove_rax_inventory_sources(apps, None)
    assert not InventorySource.objects.filter(pk=inventory_source.pk).exists()


@pytest.mark.django_db
def test_inv_src_rename(inventory_source_factory):
    inv_src01 = inventory_source_factory('t1')

    invsrc.rename_inventory_sources(apps, None)

    inv_src01.refresh_from_db()
    # inv-is-t1 is generated in the inventory_source_factory
    assert inv_src01.name == 't1 - inv-is-t1 - 0'


@pytest.mark.django_db
def test_azure_inv_src_removal(inventory_source):
    inventory_source.source = 'azure'
    inventory_source.save()

    assert InventorySource.objects.filter(pk=inventory_source.pk).exists()
    invsrc.remove_azure_inventory_sources(apps, None)
    assert not InventorySource.objects.filter(pk=inventory_source.pk).exists()


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

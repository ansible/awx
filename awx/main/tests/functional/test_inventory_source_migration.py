import pytest

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

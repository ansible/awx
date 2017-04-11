import logging

from django.db.models import Q

logger = logging.getLogger('invsrc_migrations')


def remove_manual_inventory_sources(apps, schema_editor):
    '''Previously we would automatically create inventory sources after
    Group creation and we would use the parent Group as our interface for the user.
    During that process we would create InventorySource that had a source of "manual".
    '''
    InventorySource = apps.get_model('main', 'InventorySource')
    # see models/inventory.py SOURCE_CHOICES - ('', _('Manual'))
    InventorySource.objects.filter(source='').delete()


def rename_inventory_sources(apps, schema_editor):
    '''Rename existing InventorySource entries using the following format.
    {{ inventory_source.name }} - {{ inventory.module }} - {{ number }}
    The number will be incremented for each InventorySource for the organization.
    '''
    Organization = apps.get_model('main', 'Organization')
    InventorySource = apps.get_model('main', 'InventorySource')

    for org in Organization.objects.iterator():
        for i, invsrc in enumerate(InventorySource.objects.filter(Q(inventory__organization=org) |
                                                                  Q(deprecated_group__inventory__organization=org)).distinct().all()):

            inventory = invsrc.deprecated_group.inventory if invsrc.deprecated_group else invsrc.inventory
            name = '{0} - {1} - {2}'.format(invsrc.name, inventory.name, i)
            invsrc.name = name
            invsrc.save()


def remove_inventory_source_with_no_inventory_link(apps, schema_editor):
    '''If we cannot determine the Inventory for which an InventorySource exists
    we can safely remove it.
    '''
    InventorySource = apps.get_model('main', 'InventorySource')
    InventorySource.objects.filter(Q(inventory__organization=None) & Q(deprecated_group__inventory=None)).delete()

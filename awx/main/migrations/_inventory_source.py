import logging

from django.db.models import Q
from django.utils.encoding import smart_text

from awx.main.utils.common import parse_yaml_or_json

logger = logging.getLogger('awx.main.migrations')


def remove_manual_inventory_sources(apps, schema_editor):
    '''Previously we would automatically create inventory sources after
    Group creation and we would use the parent Group as our interface for the user.
    During that process we would create InventorySource that had a source of "manual".
    '''
    # TODO: use this in the 3.3 data migrations
    InventorySource = apps.get_model('main', 'InventorySource')
    # see models/inventory.py SOURCE_CHOICES - ('', _('Manual'))
    logger.debug("Removing all Manual InventorySource from database.")
    InventorySource.objects.filter(source='').delete()


def remove_rax_inventory_sources(apps, schema_editor):
    '''Rackspace inventory sources are not supported since 3.2, remove them.
    '''
    InventorySource = apps.get_model('main', 'InventorySource')
    logger.debug("Removing all Rackspace InventorySource from database.")
    InventorySource.objects.filter(source='rax').delete()


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
            logger.debug("Renaming InventorySource({0}) {1} -> {2}".format(
                invsrc.pk, invsrc.name, name
            ))
            invsrc.name = name
            invsrc.save()


def remove_inventory_source_with_no_inventory_link(apps, schema_editor):
    '''If we cannot determine the Inventory for which an InventorySource exists
    we can safely remove it.
    '''
    InventorySource = apps.get_model('main', 'InventorySource')
    logger.debug("Removing all InventorySource that have no link to an Inventory from database.")
    InventorySource.objects.filter(Q(inventory__organization=None) & Q(deprecated_group__inventory=None)).delete()


def remove_azure_inventory_sources(apps, schema_editor):
    '''Azure inventory sources are not supported since 3.2, remove them.
    '''
    InventorySource = apps.get_model('main', 'InventorySource')
    logger.debug("Removing all Azure InventorySource from database.")
    InventorySource.objects.filter(source='azure').delete()


def _get_instance_id(from_dict, new_id, default=''):
    '''logic mostly duplicated with inventory_import command Command._get_instance_id
    frozen in time here, for purposes of migrations
    '''
    instance_id = default
    for key in new_id.split('.'):
        if not hasattr(from_dict, 'get'):
            instance_id = default
            break
        instance_id = from_dict.get(key, default)
        from_dict = instance_id
    return smart_text(instance_id)


def _get_instance_id_for_upgrade(host, new_id):
    if host.instance_id:
        # this should not have happened, but nothing to really do about it...
        logger.debug('Unexpectedly, host {}-{} has instance_id set'.format(host.name, host.pk))
        return None
    host_vars = parse_yaml_or_json(host.variables)
    new_id_value = _get_instance_id(host_vars, new_id)
    if not new_id_value:
        # another source type with overwrite_vars or pesky users could have done this
        logger.info('Host {}-{} has no {} var, probably due to separate modifications'.format(
            host.name, host.pk, new_id
        ))
        return None
    if len(new_id) > 255:
        # this should never happen
        logger.warn('Computed instance id "{}"" for host {}-{} is too long'.format(
            new_id_value, host.name, host.pk
        ))
        return None
    return new_id_value


def set_new_instance_id(apps, source, new_id):
    '''This methods adds an instance_id in cases where there was not one before
    '''
    from django.conf import settings
    id_from_settings = getattr(settings, '{}_INSTANCE_ID_VAR'.format(source.upper()))
    if id_from_settings != new_id:
        # User applied an instance ID themselves, so nope on out of there
        logger.warn('You have an instance ID set for {}, not migrating'.format(source))
        return
    logger.debug('Migrating inventory instance_id for {} to {}'.format(source, new_id))
    Host = apps.get_model('main', 'Host')
    modified_ct = 0
    for host in Host.objects.filter(inventory_sources__source=source).iterator():
        new_id_value = _get_instance_id_for_upgrade(host, new_id)
        if not new_id_value:
            continue
        host.instance_id = new_id_value
        host.save(update_fields=['instance_id'])
        modified_ct += 1
    if modified_ct:
        logger.info('Migrated instance ID for {} hosts imported by {} source'.format(
            modified_ct, source
        ))


def back_out_new_instance_id(apps, source, new_id):
    Host = apps.get_model('main', 'Host')
    modified_ct = 0
    for host in Host.objects.filter(inventory_sources__source=source).iterator():
        host_vars = parse_yaml_or_json(host.variables)
        predicted_id_value = _get_instance_id(host_vars, new_id)
        if predicted_id_value != host.instance_id:
            logger.debug('Host {}-{} did not get its instance_id from {}, skipping'.format(
                host.name, host.pk, new_id
            ))
            continue
        host.instance_id = ''
        host.save(update_fields=['instance_id'])
        modified_ct += 1
    if modified_ct:
        logger.info('Reverse migrated instance ID for {} hosts imported by {} source'.format(
            modified_ct, source
        ))


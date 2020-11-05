import logging

from uuid import uuid4

from django.utils.encoding import smart_text
from django.utils.timezone import now

from awx.main.utils.common import set_current_apps
from awx.main.utils.common import parse_yaml_or_json

logger = logging.getLogger('awx.main.migrations')


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


def delete_cloudforms_inv_source(apps, schema_editor):
    set_current_apps(apps)
    InventorySource = apps.get_model('main', 'InventorySource')
    InventoryUpdate = apps.get_model('main', 'InventoryUpdate')
    CredentialType = apps.get_model('main', 'CredentialType')
    InventoryUpdate.objects.filter(inventory_source__source='cloudforms').delete()
    InventorySource.objects.filter(source='cloudforms').delete()
    ct = CredentialType.objects.filter(namespace='cloudforms').first()
    if ct:
        ct.credentials.all().delete()
        ct.delete()

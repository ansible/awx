import logging

from uuid import uuid4

from django.utils.encoding import smart_text

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


def create_scm_script_substitute(apps, source):
    """Only applies for cloudforms in practice, but written generally.
    Given a source type, this will replace all inventory sources of that type
    with SCM inventory sources that source the script from Ansible core
    """
    # the revision in the Ansible 2.9 stable branch this project will start out as
    # it can still be updated manually later (but staying within 2.9 branch), if desired
    ansible_rev = '6f83b9aff42331e15c55a171de0a8b001208c18c'
    InventorySource = apps.get_model('main', 'InventorySource')
    Project = apps.get_model('main', 'Project')
    if not InventorySource.objects.filter(source=source).exists():
        logger.debug('No sources of type {} to migrate'.format(source))
        return
    proj_name = 'Replacement project for {} type sources - {}'.format(source, uuid4())
    project = Project(
        name=proj_name,
        description='Created by migration',
        scm_type='git',
        scm_url='https://github.com/ansible/ansible.git',
        scm_branch='stable-2.9',
        scm_revision=ansible_rev
    )
    project.save(skip_update=True)
    ct = 0
    for inv_src in InventorySource.objects.filter(source=source).iterator():
        inv_src.source = 'scm'
        inv_src.source_project = project
        inv_src.source_path = 'contrib/inventory/{}.py'.format(source)
        inv_src.scm_last_revision = ansible_rev
        inv_src.save(update_fields=['source', 'source_project', 'source_path', 'scm_last_revision'])
        logger.debug('Changed inventory source {} to scm type'.format(inv_src.pk))
        ct += 1
    if ct:
        logger.info('Changed total of {} inventory sources from {} type to scm'.format(ct, source))


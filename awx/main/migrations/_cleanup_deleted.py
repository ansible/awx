# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.db import transaction
from django.utils.dateparse import parse_datetime

def cleanup_deleted(apps, schema_editor):
    logger = logging.getLogger('awx.main.migrations.cleanup_deleted')

    def cleanup_model(model):

        '''
        Presume the '_deleted_' string to be in the 'name' field unless considering the User model.
        When considering the User model, presume the '_d_' string to be in the 'username' field.
        '''
        logger.debug('cleaning up model %s', model)

        name_field = 'name'
        name_prefix = '_deleted_'
        active_field = None
        n_deleted_items = 0
        for field in model._meta.fields:
            if field.name in ('is_active', 'active'):
                active_field = field.name
            if field.name == 'is_active': # is User model
                name_field = 'username'
                name_prefix = '_d_'
        if not active_field:
            logger.warning('skipping model %s, no active field', model)
            return n_deleted_items
        qs = model.objects.filter(**{
            active_field: False,
            '%s__startswith' % name_field: name_prefix,
        })
        pks_to_delete = set()
        for instance in qs.iterator():
            dt = parse_datetime(getattr(instance, name_field).split('_')[2])
            if not dt:
                logger.warning('unable to find deleted timestamp in %s field', name_field)
            else:
                action_text = 'deleting'
                logger.info('%s %s', action_text, instance)
                n_deleted_items += 1
                instance.delete()

            # Cleanup objects in batches instead of deleting each one individually.
            if len(pks_to_delete) >= 50:
                model.objects.filter(pk__in=pks_to_delete).delete()
                pks_to_delete.clear()
        if len(pks_to_delete):
            model.objects.filter(pk__in=pks_to_delete).delete()
        return n_deleted_items

    logger = logging.getLogger('awx.main.commands.cleanup_deleted')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    logger.propagate = False

    with transaction.atomic():
        n_deleted_items = 0

        models = [
            apps.get_model('auth', "User"),
            apps.get_model('main', 'Credential'),
            apps.get_model('main', 'CustomInventoryScript'),
            apps.get_model('main', 'Group'),
            apps.get_model('main', 'Host'),
            apps.get_model('main', 'Inventory'),
            apps.get_model('main', 'NotificationTemplate'),
            apps.get_model('main', 'Organization'),
            apps.get_model('main', 'Permission'),
            apps.get_model('main', 'Schedule'),
            apps.get_model('main', 'Team'),
            apps.get_model('main', 'UnifiedJob'),
            apps.get_model('main', 'UnifiedJobTemplate'),
        ]

        for model in models:
            n_deleted_items += cleanup_model(model)
            logger.log(99, "Removed %d items", n_deleted_items)

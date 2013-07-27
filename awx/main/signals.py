# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import logging
import threading

# Django
from django.contrib.auth.models import User
from django.db import DatabaseError
from django.db.models.signals import post_save, pre_delete, post_delete, m2m_changed
from django.dispatch import receiver

# Django-REST-Framework
from rest_framework.authtoken.models import Token

# AWX
from awx.main.models import *

__all__ = []

logger = logging.getLogger('awx.main.signals')

@receiver(post_save, sender=User)
def create_auth_token_for_user(sender, **kwargs):
    instance = kwargs.get('instance', None)
    if instance:
        try:
            Token.objects.get_or_create(user=instance)
        except DatabaseError:
            pass    
    # Only fails when creating a new superuser from syncdb on a
    # new database (before migrate has been called).


# Update has_active_failures for inventory/groups when a Host/Group is deleted
# or marked inactive, when a Host-Group or Group-Group relationship is updated,
# or when a Job is deleted or marked inactive.

_inventory_updating = threading.local()

def update_inventory_has_active_failures(sender, **kwargs):
    '''
    Signal handler and wrapper around inventory.update_has_active_failures to
    prevent unnecessary recursive calls.
    '''
    if not getattr(_inventory_updating, 'is_updating', False):
        if sender == Group.hosts.through:
            sender_name = 'group.hosts'
        elif sender == Group.parents.through:
            sender_name = 'group.parents'
        else:
            sender_name = unicode(sender._meta.verbose_name)
        if kwargs['signal'] == post_save:
            sender_action = 'saved'
        elif kwargs['signal'] == post_delete:
            sender_action = 'deleted'
        else:
            sender_action = 'changed'
        logger.debug('%s %s, updating inventory has_active_failures: %r %r',
                     sender_name, sender_action, sender, kwargs)
        try:
            _inventory_updating.is_updating = True
            inventory = kwargs['instance'].inventory
            update_hosts = issubclass(sender, Job)
            inventory.update_has_active_failures(update_hosts=update_hosts)
        finally:
            _inventory_updating.is_updating = False

post_save.connect(update_inventory_has_active_failures, sender=Host)
post_delete.connect(update_inventory_has_active_failures, sender=Host)
post_save.connect(update_inventory_has_active_failures, sender=Group)
post_delete.connect(update_inventory_has_active_failures, sender=Group)
m2m_changed.connect(update_inventory_has_active_failures, sender=Group.hosts.through)
m2m_changed.connect(update_inventory_has_active_failures, sender=Group.parents.through)
post_save.connect(update_inventory_has_active_failures, sender=Job)
post_delete.connect(update_inventory_has_active_failures, sender=Job)

# Migrate hosts, groups to parent group(s) whenever a group is deleted or
# marked as inactive.

@receiver(pre_delete, sender=Group)
def save_related_pks_before_group_delete(sender, **kwargs):
    instance = kwargs['instance']
    instance._saved_parents_pks = set(instance.parents.values_list('pk', flat=True))
    instance._saved_hosts_pks = set(instance.hosts.values_list('pk', flat=True))
    instance._saved_children_pks = set(instance.children.values_list('pk', flat=True))

@receiver(post_delete, sender=Group)
def migrate_children_from_deleted_group_to_parent_groups(sender, **kwargs):
    instance = kwargs['instance']
    parents_pks = getattr(instance, '_saved_parents_pks', [])
    hosts_pks = getattr(instance, '_saved_hosts_pks', [])
    children_pks = getattr(instance, '_saved_children_pks', [])
    for parent_group in Group.objects.filter(pk__in=parents_pks):
        for child_host in Host.objects.filter(pk__in=hosts_pks):
            logger.debug('adding host %s to parent %s after group deletion',
                         child_host, parent_group)
            parent_group.hosts.add(child_host)
        for child_group in Group.objects.filter(pk__in=children_pks):
            logger.debug('adding group %s to parent %s after group deletion',
                         child_group, parent_group)
            parent_group.children.add(child_group)

@receiver(post_save, sender=Group)
def migrate_children_from_inactive_group_to_parent_groups(sender, **kwargs):
    instance = kwargs['instance']
    if instance.active:
        return
    for parent_group in instance.parents.all():
        for child_host in instance.hosts.all():
            logger.debug('moving host %s to parent %s after making group %s inactive',
                         child_host, parent_group, instance)
            parent_group.hosts.add(child_host)
        for child_group in instance.children.all():
            logger.debug('moving group %s to parent %s after making group %s inactive',
                         child_group, parent_group, instance)
            parent_group.children.add(child_group)
        parent_group.children.remove(instance)

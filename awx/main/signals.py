# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import logging
import threading

# Django
from django.contrib.auth.models import User
from django.db import DatabaseError
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete, m2m_changed
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
        instance = kwargs['instance']
        if sender == Group.hosts.through:
            sender_name = 'group.hosts'
        elif sender == Group.parents.through:
            sender_name = 'group.parents'
        else:
            sender_name = unicode(sender._meta.verbose_name)
        if kwargs['signal'] == post_save:
            sender_action = 'saved'
            if instance.active: # No need to update for active instances.
                return
        elif kwargs['signal'] == post_delete:
            sender_action = 'deleted'
        elif kwargs['signal'] == m2m_changed and kwargs['action'] in ('post_add', 'post_remove', 'post_clear'):
            sender_action = 'changed'
        else:
            return
        logger.debug('%s %s, updating inventory has_active_failures: %r %r',
                     sender_name, sender_action, sender, kwargs)
        try:
            _inventory_updating.is_updating = True
            inventory = instance.inventory
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

@receiver(pre_save, sender=Group)
def save_related_pks_before_group_marked_inactive(sender, **kwargs):
    instance = kwargs['instance']
    if not instance.pk:
        return
    instance._saved_parents_pks = set(instance.parents.values_list('pk', flat=True))
    instance._saved_hosts_pks = set(instance.hosts.values_list('pk', flat=True))
    instance._saved_children_pks = set(instance.children.values_list('pk', flat=True))

@receiver(post_save, sender=Group)
def migrate_children_from_inactive_group_to_parent_groups(sender, **kwargs):
    instance = kwargs['instance']
    if instance.active:
        return
    parents_pks = getattr(instance, '_saved_parents_pks', [])
    hosts_pks = getattr(instance, '_saved_hosts_pks', [])
    children_pks = getattr(instance, '_saved_children_pks', [])
    for parent_group in Group.objects.filter(pk__in=parents_pks):
        for child_host in Host.objects.filter(pk__in=hosts_pks):
            logger.debug('moving host %s to parent %s after marking group %s inactive',
                         child_host, parent_group, instance)
            parent_group.hosts.add(child_host)
        for child_group in Group.objects.filter(pk__in=children_pks):
            logger.debug('moving group %s to parent %s after marking group %s inactive',
                         child_group, parent_group, instance)
            parent_group.children.add(child_group)
        parent_group.children.remove(instance)

# Update host pointers to last_job and last_job_host_summary when a job is
# marked inactive or deleted.

def _update_host_last_jhs(host):
    jhs_qs = JobHostSummary.objects.filter(job__active=True, host__pk=host.pk)
    try:
        jhs = jhs_qs.order_by('-job__pk')[0]
    except IndexError:
        jhs = None
    update_fields = []
    last_job = jhs.job if jhs else None
    if host.last_job != last_job:
        host.last_job = last_job
        update_fields.append('last_job')
    if host.last_job_host_summary != jhs:
        host.last_job_host_summary = jhs
        update_fields.append('last_job_host_summary')
    if update_fields:
        host.save(update_fields=update_fields)

@receiver(post_save, sender=Job)
def update_host_last_job_when_job_marked_inactive(sender, **kwargs):
    instance = kwargs['instance']
    hosts_qs = Host.objects.filter(active=True, last_job__pk=instance.pk)
    for host in hosts_qs:
        _update_host_last_jhs(host)

@receiver(pre_delete, sender=Job)
def save_host_pks_before_job_delete(sender, **kwargs):
    instance = kwargs['instance']
    hosts_qs = Host.objects.filter(active=True, last_job__pk=instance.pk)
    instance._saved_hosts_pks = set(hosts_qs.values_list('pk', flat=True))

@receiver(post_delete, sender=Job)
def update_host_last_job_after_job_deleted(sender, **kwargs):
    instance = kwargs['instance']
    hosts_pks = getattr(instance, '_saved_hosts_pks', [])
    for host in Host.objects.filter(pk__in=hosts_pks):
        _update_host_last_jhs(host)

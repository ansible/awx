# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import logging
import threading

# Django
from django.contrib.auth.models import User
from django.db import DatabaseError
from django.db.models.signals import post_save, post_delete, m2m_changed
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

# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.


from django.db import models

class ActivityStream(models.Model):
    '''
    Model used to describe activity stream (audit) events
    '''
    OPERATION_CHOICES = [
        ('create', _('Entity Created')),
        ('update', _("Entity Updated")),
        ('delete', _("Entity Deleted")),
        ('associate', _("Entity Associated with another Entity")),
        ('disaassociate', _("Entity was Disassociated with another Entity"))
    ]

    user = models.ForeignKey('auth.User', null=True, on_delete=models.SET_NULL)
    operation = models.CharField(max_length=9, choices=OPERATION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.TextField(blank=True)

    object1_id = models.PositiveIntegerField(db_index=True)
    object1_type = models.TextField()

    object2_id = models.PositiveIntegerField(db_index=True)
    object2_type = models.TextField()

    object_relationship_type = models.TextField()

# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.


from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

class ActivityStream(models.Model):
    '''
    Model used to describe activity stream (audit) events
    '''

    class Meta:
        app_label = 'main'

    OPERATION_CHOICES = [
        ('create', _('Entity Created')),
        ('update', _("Entity Updated")),
        ('delete', _("Entity Deleted")),
        ('associate', _("Entity Associated with another Entity")),
        ('disassociate', _("Entity was Disassociated with another Entity"))
    ]

    user = models.ForeignKey('auth.User', null=True, on_delete=models.SET_NULL, related_name='activity_stream')
    operation = models.CharField(max_length=13, choices=OPERATION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.TextField(blank=True)

    object1_id = models.PositiveIntegerField(db_index=True)
    object1 = models.TextField()
    object1_type = models.TextField()

    object2_id = models.PositiveIntegerField(db_index=True, null=True)
    object2 = models.TextField(null=True, blank=True)
    object2_type = models.TextField(null=True, blank=True)

    object_relationship_type = models.TextField(blank=True)

    def get_absolute_url(self):
        return reverse('api:activity_stream_detail', args=(self.pk,))

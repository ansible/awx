# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Django
from django.conf import settings
from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

__all__ = ['ActivityStream']


class ActivityStreamBase(models.Model):
    '''
    Model used to describe activity stream (audit) events
    '''

    class Meta:
        abstract = True
        app_label = 'main'

    OPERATION_CHOICES = [
        ('create', _('Entity Created')),
        ('update', _("Entity Updated")),
        ('delete', _("Entity Deleted")),
        ('associate', _("Entity Associated with another Entity")),
        ('disassociate', _("Entity was Disassociated with another Entity"))
    ]

    actor = models.ForeignKey('auth.User', null=True, on_delete=models.SET_NULL, related_name='activity_stream')
    operation = models.CharField(max_length=13, choices=OPERATION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.TextField(blank=True)

    object_relationship_type = models.TextField(blank=True)
    object1 = models.TextField()
    object2 = models.TextField()

    user = models.ManyToManyField("auth.User", blank=True)
    organization = models.ManyToManyField("Organization", blank=True)
    inventory = models.ManyToManyField("Inventory", blank=True)
    host = models.ManyToManyField("Host", blank=True)
    group = models.ManyToManyField("Group", blank=True)
    #inventory_source = models.ManyToManyField("InventorySource", blank=True)
    #inventory_update = models.ManyToManyField("InventoryUpdate", blank=True)
    credential = models.ManyToManyField("Credential", blank=True)
    team = models.ManyToManyField("Team", blank=True)
    #project = models.ManyToManyField("Project", blank=True)
    #project_update = models.ManyToManyField("ProjectUpdate", blank=True)
    permission = models.ManyToManyField("Permission", blank=True)
    #job_template = models.ManyToManyField("JobTemplate", blank=True)
    #job = models.ManyToManyField("Job", blank=True)
    schedule = models.ManyToManyField("Schedule", blank=True)

    def get_absolute_url(self):
        return reverse('api:activity_stream_detail', args=(self.pk,))

    def save(self, *args, **kwargs):
        # For compatibility with Django 1.4.x, attempt to handle any calls to
        # save that pass update_fields.
        try:
            super(ActivityStreamBase, self).save(*args, **kwargs)
        except TypeError:
            if 'update_fields' not in kwargs:
                raise
            kwargs.pop('update_fields')
            super(ActivityStreamBase, self).save(*args, **kwargs)


if getattr(settings, 'UNIFIED_JOBS_STEP') == 0:

    class ActivityStream(ActivityStreamBase):
        
        class Meta:
            app_label = 'main'

        inventory_source = models.ManyToManyField("InventorySource", blank=True)
        inventory_update = models.ManyToManyField("InventoryUpdate", blank=True)
        project = models.ManyToManyField("Project", blank=True)
        project_update = models.ManyToManyField("ProjectUpdate", blank=True)
        job_template = models.ManyToManyField("JobTemplate", blank=True)
        job = models.ManyToManyField("Job", blank=True)

        unified_job_template = models.ManyToManyField("UnifiedJobTemplate", blank=True, related_name='activity_stream_as_unified_job_template+')
        unified_job = models.ManyToManyField("UnifiedJob", blank=True, related_name='activity_stream_as_unified_job+')

        new_inventory_source = models.ManyToManyField("InventorySourceNew", blank=True)
        new_inventory_update = models.ManyToManyField("InventoryUpdateNew", blank=True)
        new_project = models.ManyToManyField("ProjectNew", blank=True)
        new_project_update = models.ManyToManyField("ProjectUpdateNew", blank=True)
        new_job_template = models.ManyToManyField("JobTemplateNew", blank=True)
        new_job = models.ManyToManyField("JobNew", blank=True)

if getattr(settings, 'UNIFIED_JOBS_STEP') == 1:
    
    class ActivityStream(ActivityStreamBase):
        
        class Meta:
            app_label = 'main'

        unified_job_template = models.ManyToManyField("UnifiedJobTemplate", blank=True, related_name='activity_stream_as_unified_job_template+')
        unified_job = models.ManyToManyField("UnifiedJob", blank=True, related_name='activity_stream_as_unified_job+')

        new_inventory_source = models.ManyToManyField("InventorySourceNew", blank=True)
        new_inventory_update = models.ManyToManyField("InventoryUpdateNew", blank=True)
        new_project = models.ManyToManyField("ProjectNew", blank=True)
        new_project_update = models.ManyToManyField("ProjectUpdateNew", blank=True)
        new_job_template = models.ManyToManyField("JobTemplateNew", blank=True)
        new_job = models.ManyToManyField("JobNew", blank=True)

if getattr(settings, 'UNIFIED_JOBS_STEP') == 2:

    class ActivityStream(ActivityStreamBase):

        class Meta:
            app_label = 'main'

        unified_job_template = models.ManyToManyField("UnifiedJobTemplate", blank=True, related_name='activity_stream_as_unified_job_template+')
        unified_job = models.ManyToManyField("UnifiedJob", blank=True, related_name='activity_stream_as_unified_job+')

        inventory_source = models.ManyToManyField("InventorySource", blank=True)
        inventory_update = models.ManyToManyField("InventoryUpdate", blank=True)
        project = models.ManyToManyField("Project", blank=True)
        project_update = models.ManyToManyField("ProjectUpdate", blank=True)
        job_template = models.ManyToManyField("JobTemplate", blank=True)
        job = models.ManyToManyField("Job", blank=True)

# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Tower
from awx.api.versioning import reverse
from awx.main.fields import JSONField

# Django
from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ['ActivityStream']


class ActivityStream(models.Model):
    '''
    Model used to describe activity stream (audit) events
    '''

    class Meta:
        app_label = 'main'
        ordering = ('pk',)

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
    inventory_source = models.ManyToManyField("InventorySource", blank=True)
    inventory_update = models.ManyToManyField("InventoryUpdate", blank=True)
    credential = models.ManyToManyField("Credential", blank=True)
    credential_type = models.ManyToManyField("CredentialType", blank=True)
    team = models.ManyToManyField("Team", blank=True)
    project = models.ManyToManyField("Project", blank=True)
    project_update = models.ManyToManyField("ProjectUpdate", blank=True)
    job_template = models.ManyToManyField("JobTemplate", blank=True)
    job = models.ManyToManyField("Job", blank=True)
    workflow_job_template_node = models.ManyToManyField("WorkflowJobTemplateNode", blank=True)
    workflow_job_node = models.ManyToManyField("WorkflowJobNode", blank=True)
    workflow_job_template = models.ManyToManyField("WorkflowJobTemplate", blank=True)
    workflow_job = models.ManyToManyField("WorkflowJob", blank=True)
    unified_job_template = models.ManyToManyField("UnifiedJobTemplate", blank=True, related_name='activity_stream_as_unified_job_template+')
    unified_job = models.ManyToManyField("UnifiedJob", blank=True, related_name='activity_stream_as_unified_job+')
    ad_hoc_command = models.ManyToManyField("AdHocCommand", blank=True)
    schedule = models.ManyToManyField("Schedule", blank=True)
    custom_inventory_script = models.ManyToManyField("CustomInventoryScript", blank=True)
    notification_template = models.ManyToManyField("NotificationTemplate", blank=True)
    notification = models.ManyToManyField("Notification", blank=True)
    label = models.ManyToManyField("Label", blank=True)
    role = models.ManyToManyField("Role", blank=True)
    instance_group = models.ManyToManyField("InstanceGroup", blank=True)
    application = models.ManyToManyField("oauth2_provider.Application", blank=True)
    access_token = models.ManyToManyField("oauth2_provider.AccessToken", blank=True)

    setting = JSONField(blank=True)

    def get_absolute_url(self, request=None):
        return reverse('api:activity_stream_detail', kwargs={'pk': self.pk}, request=request)

    def save(self, *args, **kwargs):
        # For compatibility with Django 1.4.x, attempt to handle any calls to
        # save that pass update_fields.
        try:
            super(ActivityStream, self).save(*args, **kwargs)
        except TypeError:
            if 'update_fields' not in kwargs:
                raise
            kwargs.pop('update_fields')
            super(ActivityStream, self).save(*args, **kwargs)

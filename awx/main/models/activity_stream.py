# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Tower
from awx.api.versioning import reverse
from awx.main.fields import JSONField
from awx.main.models.base import accepts_json

# Django
from django.db import models
from django.conf import settings
from django.utils.encoding import smart_str
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
    changes = accepts_json(models.TextField(blank=True))
    deleted_actor = JSONField(null=True)
    action_node = models.CharField(
        blank=True,
        default='',
        editable=False,
        max_length=512,
        help_text=_("The cluster node the activity took place on."),
    )

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
    workflow_approval_template = models.ManyToManyField("WorkflowApprovalTemplate", blank=True)
    workflow_approval = models.ManyToManyField("WorkflowApproval", blank=True)
    unified_job_template = models.ManyToManyField("UnifiedJobTemplate", blank=True, related_name='activity_stream_as_unified_job_template+')
    unified_job = models.ManyToManyField("UnifiedJob", blank=True, related_name='activity_stream_as_unified_job+')
    ad_hoc_command = models.ManyToManyField("AdHocCommand", blank=True)
    schedule = models.ManyToManyField("Schedule", blank=True)
    custom_inventory_script = models.ManyToManyField("CustomInventoryScript", blank=True)
    notification_template = models.ManyToManyField("NotificationTemplate", blank=True)
    notification = models.ManyToManyField("Notification", blank=True)
    label = models.ManyToManyField("Label", blank=True)
    role = models.ManyToManyField("Role", blank=True)
    instance = models.ManyToManyField("Instance", blank=True)
    instance_group = models.ManyToManyField("InstanceGroup", blank=True)
    o_auth2_application = models.ManyToManyField("OAuth2Application", blank=True)
    o_auth2_access_token = models.ManyToManyField("OAuth2AccessToken", blank=True)



    setting = JSONField(blank=True)

    def __str__(self):
        operation = self.operation if 'operation' in self.__dict__ else '_delayed_'
        if 'timestamp' in self.__dict__:
            if self.timestamp:
                timestamp = self.timestamp.isoformat()
            else:
                timestamp = self.timestamp
        else:
            timestamp = '_delayed_'
        return u'%s-%s-pk=%s' % (operation, timestamp, self.pk)

    def get_absolute_url(self, request=None):
        return reverse('api:activity_stream_detail', kwargs={'pk': self.pk}, request=request)

    def save(self, *args, **kwargs):
        # Store denormalized actor metadata so that we retain it for accounting
        # purposes when the User row is deleted.
        if self.actor:
            self.deleted_actor = {
                'id': self.actor_id,
                'username': smart_str(self.actor.username),
                'first_name': smart_str(self.actor.first_name),
                'last_name': smart_str(self.actor.last_name),
            }
            if 'update_fields' in kwargs and 'deleted_actor' not in kwargs['update_fields']:
                kwargs['update_fields'].append('deleted_actor')

        hostname_char_limit = self._meta.get_field('action_node').max_length
        self.action_node = settings.CLUSTER_HOST_ID[:hostname_char_limit]

        super(ActivityStream, self).save(*args, **kwargs)

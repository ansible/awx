# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db import models
from django.core.urlresolvers import reverse
#from django import settings as tower_settings

# AWX
from awx.main.models import UnifiedJobTemplate, UnifiedJob
from awx.main.models.base import BaseModel, CreatedModifiedModel, VarsDictProperty
from awx.main.models.rbac import (
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
)
from awx.main.fields import ImplicitRoleField

__all__ = ['WorkflowJobTemplate', 'WorkflowJob', 'WorkflowJobOptions', 'WorkflowNode']

class WorkflowNode(CreatedModifiedModel):

    class Meta:
        app_label = 'main'

    # TODO: RBAC
    '''
    admin_role = ImplicitRoleField(
        parent_role='workflow_job_template.admin_role',
    )
    '''

    workflow_job_template = models.ForeignKey(
        'WorkflowJobTemplate',
        related_name='workflow_nodes',
        on_delete=models.CASCADE,
    )
    unified_job_template = models.ForeignKey(
        'UnifiedJobTemplate',
        related_name='unified_jt_workflow_nodes',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    success_nodes = models.ManyToManyField(
        'self',
        related_name='parent_success_nodes',
        blank=True,
        symmetrical=False,
    )
    failure_nodes = models.ManyToManyField(
        'self',
        related_name='parent_failure_nodes',
        blank=True,
        symmetrical=False,
    )
    always_nodes = models.ManyToManyField(
        'self',
        related_name='parent_always_nodes',
        blank=True,
        symmetrical=False,
    )
    job = models.ForeignKey(
        'UnifiedJob',
        related_name='workflow_node',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    
    def get_absolute_url(self):
        return reverse('api:workflow_node_detail', args=(self.pk,))

class WorkflowJobOptions(BaseModel):
    class Meta:
        abstract = True

    extra_vars = models.TextField(
        blank=True,
        default='',
    )

class WorkflowJobTemplate(UnifiedJobTemplate, WorkflowJobOptions):

    class Meta:
        app_label = 'main'

    admin_role = ImplicitRoleField(
        parent_role='singleton:' + ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    )

    @classmethod
    def _get_unified_job_class(cls):
        return WorkflowJob

    @classmethod
    def _get_unified_job_field_names(cls):
        # TODO: ADD LABELS
        return ['name', 'description', 'extra_vars', 'workflow_nodes']

    def get_absolute_url(self):
        return reverse('api:workflow_job_template_detail', args=(self.pk,))

    @property
    def cache_timeout_blocked(self):
        # TODO: don't allow running of job template if same workflow template running
        return False

    # TODO: Notifications
    # TODO: Surveys

    def create_job(self, **kwargs):
        '''
        Create a new job based on this template.
        '''
        return self.create_unified_job(**kwargs)


class WorkflowJob(UnifiedJob, WorkflowJobOptions):

    class Meta:
        app_label = 'main'
        ordering = ('id',)

    workflow_job_template = models.ForeignKey(
        'WorkflowJobTemplate',
        related_name='jobs',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    extra_vars_dict = VarsDictProperty('extra_vars', True)

    @classmethod
    def _get_parent_field_name(cls):
        return 'workflow_job_template'

    @classmethod
    def _get_task_class(cls):
        from awx.main.tasks import RunWorkflowJob
        return RunWorkflowJob

    def socketio_emit_data(self):
        return {}

    def get_absolute_url(self):
        return reverse('api:workflow_job_detail', args=(self.pk,))

    def get_ui_url(self):
        return urljoin(tower_settings.TOWER_URL_BASE, "/#/workflow_jobs/{}".format(self.pk))

    def is_blocked_by(self, obj):
        return True

    @property
    def task_impact(self):
        return 0


# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
#import urlparse

# Django
from django.db import models
from django.core.urlresolvers import reverse
#from django import settings as tower_settings

from jsonfield import JSONField

# AWX
from awx.main.models import UnifiedJobTemplate, UnifiedJob
from awx.main.models.notifications import JobNotificationMixin
from awx.main.models.base import BaseModel, CreatedModifiedModel, VarsDictProperty
from awx.main.models.rbac import (
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    ROLE_SINGLETON_SYSTEM_AUDITOR
)
from awx.main.fields import ImplicitRoleField
from awx.main.models.mixins import ResourceMixin

import yaml
import json

__all__ = ['WorkflowJobTemplate', 'WorkflowJob', 'WorkflowJobOptions', 'WorkflowJobNode', 'WorkflowJobTemplateNode',]

CHAR_PROMPTS_LIST = ['job_type', 'job_tags', 'skip_tags', 'limit', 'skip_tags']

class WorkflowNodeBase(CreatedModifiedModel):
    class Meta:
        abstract = True
        app_label = 'main'

    success_nodes = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='%(class)ss_success',
    )
    failure_nodes = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='%(class)ss_failure',
    )
    always_nodes = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='%(class)ss_always',
    )
    unified_job_template = models.ForeignKey(
        'UnifiedJobTemplate',
        related_name='%(class)ss',
        blank=False,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    # Prompting-related fields
    inventory = models.ForeignKey(
        'Inventory',
        related_name='%(class)ss',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='%(class)ss',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    char_prompts = JSONField(
        blank=True,
        default={}
    )

    def prompts_dict(self):
        data = {}
        if self.inventory:
            data['inventory'] = self.inventory
        if self.credential:
            data['credential'] = self.credential
        for fd in CHAR_PROMPTS_LIST:
            if fd in self.char_prompts:
                data[fd] = self.char_prompts[fd]
        return data

    def get_prompts_warnings(self):
        ujt_obj = self.unified_job_template
        if ujt_obj is None:
            return {}
        prompts_dict = self.prompts_dict()
        from awx.main.models import JobTemplate
        if not isinstance(ujt_obj, JobTemplate):
            return {'ignored': {'all': 'Can not use prompts on unified_job_template that is not type of job template'}}
        ask_for_vars_dict = ujt_obj._ask_for_vars_dict()
        ignored_dict = {}
        missing_dict = {}
        for fd in prompts_dict:
            if not ask_for_vars_dict[fd]:
                ignored_dict[fd] = 'Workflow node provided field, but job template is not set to ask on launch'
        for fd in ask_for_vars_dict:
            ujt_field = getattr(ujt_obj, fd)
            if ujt_field is None and prompts_dict.get(fd, None) is None:
                missing_dict[fd] = 'Job Template does not have this field and workflow node does not provide it'
        data = {}
        if ignored_dict:
            data.update(ignored_dict)
        if missing_dict:
            data.update(missing_dict)
        return data

class WorkflowJobTemplateNode(WorkflowNodeBase):
    # TODO: Ensure the API forces workflow_job_template being set
    workflow_job_template = models.ForeignKey(
        'WorkflowJobTemplate',
        related_name='workflow_job_template_nodes',
        blank=True,
        null=True,
        default=None,
        on_delete=models.CASCADE,
    )
    
    def get_absolute_url(self):
        return reverse('api:workflow_job_template_node_detail', args=(self.pk,))

class WorkflowJobNode(WorkflowNodeBase):
    job = models.ForeignKey(
        'UnifiedJob',
        related_name='unified_job_nodes',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    workflow_job = models.ForeignKey(
        'WorkflowJob',
        related_name='workflow_job_nodes',
        blank=True,
        null=True,
        default=None,
        on_delete=models.CASCADE,
    )
    
    def get_absolute_url(self):
        return reverse('api:workflow_job_node_detail', args=(self.pk,))

    def get_job_kwargs(self):
        data = {}
        # rejecting/accepting prompting variables done with the node copy
        if self.inventory:
            data['inventory'] = self.inventory
        if self.credential:
            data['credential'] = self.credential
        if self.char_prompts:
            data.update(self.char_prompts)
        # process extra_vars
        extra_vars = {}
        if self.workflow_job and self.workflow_job.extra_vars:
            try:
                WJ_json_extra_vars = json.loads(
                    (self.workflow_job.extra_vars or '').strip() or '{}')
            except ValueError:
                try:
                    WJ_json_extra_vars = yaml.safe_load(self.workflow_job.extra_vars)
                except yaml.YAMLError:
                    WJ_json_extra_vars = {}
        extra_vars.update(WJ_json_extra_vars)
        # TODO: merge artifacts, add ancestor_artifacts to kwargs
        if extra_vars:
            data['extra_vars'] = extra_vars
        return data

class WorkflowJobOptions(BaseModel):
    class Meta:
        abstract = True

    extra_vars = models.TextField(
        blank=True,
        default='',
    )

class WorkflowJobTemplate(UnifiedJobTemplate, WorkflowJobOptions, ResourceMixin):

    class Meta:
        app_label = 'main'

    organization = models.ForeignKey(
        'Organization',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='workflows',
    )
    admin_role = ImplicitRoleField(parent_role=[
        'singleton:' + ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
        'organization.admin_role'
    ])
    execute_role = ImplicitRoleField(parent_role=[
        'admin_role'
    ])
    read_role = ImplicitRoleField(parent_role=[
        'singleton:' + ROLE_SINGLETON_SYSTEM_AUDITOR,
        'organization.auditor_role', 'execute_role', 'admin_role'
    ])

    @classmethod
    def _get_unified_job_class(cls):
        return WorkflowJob

    @classmethod
    def _get_unified_job_field_names(cls):
        # TODO: ADD LABELS
        return ['name', 'description', 'extra_vars',]

    def get_absolute_url(self):
        return reverse('api:workflow_job_template_detail', args=(self.pk,))

    @property
    def cache_timeout_blocked(self):
        # TODO: don't allow running of job template if same workflow template running
        return False

    # TODO: Notifications
    # TODO: Surveys

    #def create_job(self, **kwargs):
    #    '''
    #    Create a new job based on this template.
    #    '''
    #    return self.create_unified_job(**kwargs)

    # TODO: Delete create_unified_job here and explicitly call create_workflow_job() .. figure out where the call is
    def create_unified_job(self, **kwargs):

        #def create_workflow_job(self, **kwargs):
        #workflow_job =  self.create_unified_job(**kwargs)
        workflow_job = super(WorkflowJobTemplate, self).create_unified_job(**kwargs)
        workflow_job.inherit_job_template_workflow_nodes()
        return workflow_job

    def get_warnings(self):
        warning_data = {}
        for node in self.workflow_job_template_nodes.all():
            if node.unified_job_template is None:
                warning_data[node.pk] = 'Node is missing a linked unified_job_template'
                continue
            node_prompts_warnings = node.get_prompts_warnings()
            if node_prompts_warnings:
                warning_data[node.pk] = node_prompts_warnings
        return warning_data

class WorkflowJobInheritNodesMixin(object):
    def _inherit_relationship(self, old_node, new_node, node_ids_map, node_type):
        old_related_nodes = self._get_all_by_type(old_node, node_type)
        new_node_type_mgr = getattr(new_node, node_type)

        for old_related_node in old_related_nodes:
            new_related_node = self._get_workflow_job_node_by_id(node_ids_map[old_related_node.id])
            new_node_type_mgr.add(new_related_node)

    '''
    Create a WorkflowJobNode for each WorkflowJobTemplateNode
    '''
    def _create_workflow_job_nodes(self, old_nodes):
        new_node_list = []
        for old_node in old_nodes:
            kwargs = dict(
                workflow_job=self,
                unified_job_template=old_node.unified_job_template,
            )
            ujt_obj = old_node.unified_job_template
            if ujt_obj:
                ask_for_vars_dict = ujt_obj._ask_for_vars_dict()
                if ask_for_vars_dict['inventory'] and old_node.inventory:
                    kwargs['inventory'] = old_node.inventory
                if ask_for_vars_dict['credential'] and old_node.credential:
                    kwargs['credential'] = old_node.credential
                for fd in CHAR_PROMPTS_LIST:
                    new_char_prompts = {}
                    if ask_for_vars_dict[fd] and old_node.char_prompts.get(fd, None):
                        new_char_prompts[fd] = old_node.char_prompts[fd]
                    if new_char_prompts:
                        kwargs['char_prompts'] = new_char_prompts
            new_node_list.append(WorkflowJobNode.objects.create(**kwargs))
        return new_node_list

    def _map_workflow_job_nodes(self, old_nodes, new_nodes):
        node_ids_map = {}

        for i, old_node in enumerate(old_nodes):
            node_ids_map[old_node.id] = new_nodes[i].id

        return node_ids_map

    def _get_workflow_job_template_nodes(self):
        return self.workflow_job_template.workflow_job_template_nodes.all()

    def _get_workflow_job_node_by_id(self, id):
        return WorkflowJobNode.objects.get(id=id)

    def _get_all_by_type(self, node, node_type):
        return getattr(node, node_type).all()

    def inherit_job_template_workflow_nodes(self):
        old_nodes = self._get_workflow_job_template_nodes()
        new_nodes = self._create_workflow_job_nodes(old_nodes)
        node_ids_map = self._map_workflow_job_nodes(old_nodes, new_nodes)

        for index, old_node in enumerate(old_nodes):
            new_node = new_nodes[index]
            for node_type in ['success_nodes', 'failure_nodes', 'always_nodes']:
                self._inherit_relationship(old_node, new_node, node_ids_map, node_type)
                

class WorkflowJob(UnifiedJob, WorkflowJobOptions, JobNotificationMixin, WorkflowJobInheritNodesMixin):

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

    # TODO: Ask UI if this is needed ?
    #def get_ui_url(self):
    #    return urlparse.urljoin(tower_settings.TOWER_URL_BASE, "/#/workflow_jobs/{}".format(self.pk))

    def is_blocked_by(self, obj):
        return True

    @property
    def task_impact(self):
        return 0

    # TODO: workflow job notifications
    def get_notification_templates(self):
        return []

    # TODO: workflow job notifications
    def get_notification_friendly_name(self):
        return "Workflow Job"


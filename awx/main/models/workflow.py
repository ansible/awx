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
from awx.main.redact import REPLACE_STR

from copy import copy

__all__ = ['WorkflowJobTemplate', 'WorkflowJob', 'WorkflowJobOptions', 'WorkflowJobNode', 'WorkflowJobTemplateNode',]

CHAR_PROMPTS_LIST = ['job_type', 'job_tags', 'skip_tags', 'limit']

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
            data['inventory'] = self.inventory.pk
        if self.credential:
            data['credential'] = self.credential.pk
        for fd in CHAR_PROMPTS_LIST:
            if fd in self.char_prompts:
                data[fd] = self.char_prompts[fd]
        return data

    @property
    def job_type(self):
        return self.char_prompts.get('job_type', None)

    @property
    def job_tags(self):
        return self.char_prompts.get('job_tags', None)

    @property
    def skip_tags(self):
        return self.char_prompts.get('skip_tags', None)

    @property
    def limit(self):
        return self.char_prompts.get('limit', None)

    def get_prompts_warnings(self):
        ujt_obj = self.unified_job_template
        if ujt_obj is None:
            return {}
        prompts_dict = self.prompts_dict()
        if not hasattr(ujt_obj, '_ask_for_vars_dict'):
            if prompts_dict:
                return {'ignored': {'all': 'Can not use prompts on unified_job_template that is not type of job template'}}
            else:
                return {}

        accepted_fields, ignored_fields = ujt_obj._accept_or_ignore_job_kwargs(**prompts_dict)
        ask_for_vars_dict = ujt_obj._ask_for_vars_dict()

        ignored_dict = {}
        missing_dict = {}
        for fd in ignored_fields:
            ignored_dict[fd] = 'Workflow node provided field, but job template is not set to ask on launch'
        scan_errors = ujt_obj._extra_job_type_errors(accepted_fields)
        ignored_dict.update(scan_errors)
        for fd in ['inventory', 'credential']:
            if getattr(ujt_obj, fd) is None and not (ask_for_vars_dict.get(fd, False) and fd in prompts_dict):
                missing_dict[fd] = 'Job Template does not have this field and workflow node does not provide it'

        data = {}
        if ignored_dict:
            data['ignored'] = ignored_dict
        if missing_dict:
            data['missing'] = missing_dict
        return data

    def get_parent_nodes(self):
        '''Returns queryset containing all parents of this node'''
        success_parents = getattr(self, '%ss_success' % self.__class__.__name__.lower()).all()
        failure_parents = getattr(self, '%ss_failure' % self.__class__.__name__.lower()).all()
        always_parents = getattr(self, '%ss_always' % self.__class__.__name__.lower()).all()
        return success_parents | failure_parents | always_parents

    @classmethod
    def _get_workflow_job_field_names(cls):
        '''
        Return field names that should be copied from template node to job node.
        '''
        return ['workflow_job', 'unified_job_template',
                'inventory', 'credential', 'char_prompts']

class WorkflowJobTemplateNode(WorkflowNodeBase):
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

    def create_workflow_job_node(self, **kwargs):
        '''
        Create a new workflow job node based on this workflow node.
        '''
        create_kwargs = {}
        for field_name in self._get_workflow_job_field_names():
            if field_name in kwargs:
                create_kwargs[field_name] = kwargs[field_name]
            elif hasattr(self, field_name):
                create_kwargs[field_name] = getattr(self, field_name)
        return WorkflowJobNode.objects.create(**create_kwargs)

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
    ancestor_artifacts = JSONField(
        blank=True,
        default={},
        editable=False,
    )
    
    def get_absolute_url(self):
        return reverse('api:workflow_job_node_detail', args=(self.pk,))

    def get_job_kwargs(self):
        '''
        In advance of creating a new unified job as part of a workflow,
        this method builds the attributes to use
        It alters the node by saving its updated version of
        ancestor_artifacts, making it available to subsequent nodes.
        '''
        # reject/accept prompted fields
        data = {}
        ujt_obj = self.unified_job_template
        if ujt_obj and hasattr(ujt_obj, '_ask_for_vars_dict'):
            accepted_fields, ignored_fields = ujt_obj._accept_or_ignore_job_kwargs(**self.prompts_dict())
            for fd in ujt_obj._extra_job_type_errors(accepted_fields):
                accepted_fields.pop(fd)
            data.update(accepted_fields)
            # TODO: decide what to do in the event of missing fields
        # build ancestor artifacts, save them to node model for later
        aa_dict = {}
        for parent_node in self.get_parent_nodes():
            aa_dict.update(parent_node.ancestor_artifacts)
            if parent_node.job and hasattr(parent_node.job, 'artifacts'):
                aa_dict.update(parent_node.job.artifacts)
        if aa_dict:
            self.ancestor_artifacts = aa_dict
            self.save(update_fields=['ancestor_artifacts'])
        if '_ansible_no_log' in aa_dict:
            # TODO: merge Workflow Job survey passwords into this
            password_dict = {}
            for key in aa_dict:
                if key != '_ansible_no_log':
                    password_dict[key] = REPLACE_STR
            data['survey_passwords'] = password_dict
        # process extra_vars
        # TODO: still lack consensus about variable precedence
        extra_vars = {}
        if self.workflow_job and self.workflow_job.extra_vars:
            extra_vars.update(self.workflow_job.extra_vars_dict)
        if aa_dict:
            functional_aa_dict = copy(aa_dict)
            functional_aa_dict.pop('_ansible_no_log', None)
            extra_vars.update(functional_aa_dict)
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
        return ['name', 'description', 'extra_vars', 'labels', 'schedule', 'launch_type']

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
        return [old_node.create_workflow_job_node(workflow_job=self) for old_node in old_nodes]

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

    def _has_failed(self):
        return False

    def socketio_emit_data(self):
        return {}

    def get_absolute_url(self):
        return reverse('api:workflow_job_detail', args=(self.pk,))

    # TODO: Ask UI if this is needed ?
    #def get_ui_url(self):
    #    return urlparse.urljoin(tower_settings.TOWER_URL_BASE, "/#/workflow_jobs/{}".format(self.pk))

    @property
    def task_impact(self):
        return 0

    # TODO: workflow job notifications
    def get_notification_templates(self):
        return []

    # TODO: workflow job notifications
    def get_notification_friendly_name(self):
        return "Workflow Job"

    '''
    A WorkflowJob is a virtual job. It doesn't result in a celery task.
    '''
    def start_celery_task(self, opts, error_callback, success_callback):
        return None

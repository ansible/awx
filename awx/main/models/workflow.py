# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
#import urlparse

# Django
from django.db import models
from django.conf import settings
#from django import settings as tower_settings

# AWX
from awx.api.versioning import reverse
from awx.main.models import prevent_search, UnifiedJobTemplate, UnifiedJob
from awx.main.models.notifications import (
    NotificationTemplate,
    JobNotificationMixin
)
from awx.main.models.base import BaseModel, CreatedModifiedModel, VarsDictProperty
from awx.main.models.rbac import (
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    ROLE_SINGLETON_SYSTEM_AUDITOR
)
from awx.main.fields import ImplicitRoleField
from awx.main.models.mixins import ResourceMixin, SurveyJobTemplateMixin, SurveyJobMixin
from awx.main.redact import REPLACE_STR
from awx.main.utils import parse_yaml_or_json
from awx.main.fields import JSONField

from copy import copy
from urlparse import urljoin

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
                return {'ignored': {'all': 'Cannot use prompts on unified_job_template that is not type of job template'}}
            else:
                return {}

        accepted_fields, ignored_fields = ujt_obj._accept_or_ignore_job_kwargs(**prompts_dict)

        ignored_dict = {}
        for fd in ignored_fields:
            ignored_dict[fd] = 'Workflow node provided field, but job template is not set to ask on launch'
        scan_errors = ujt_obj._extra_job_type_errors(accepted_fields)
        ignored_dict.update(scan_errors)

        data = {}
        if ignored_dict:
            data['ignored'] = ignored_dict
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


class WorkflowJobTemplateNode(WorkflowNodeBase):
    workflow_job_template = models.ForeignKey(
        'WorkflowJobTemplate',
        related_name='workflow_job_template_nodes',
        blank=True,
        null=True,
        default=None,
        on_delete=models.CASCADE,
    )

    def get_absolute_url(self, request=None):
        return reverse('api:workflow_job_template_node_detail', kwargs={'pk': self.pk}, request=request)

    def create_wfjt_node_copy(self, user, workflow_job_template=None):
        '''
        Copy this node to a new WFJT, leaving out related fields the user
        is not allowed to access
        '''
        create_kwargs = {}
        for field_name in self._get_workflow_job_field_names():
            item = getattr(self, field_name, None)
            if item is None:
                continue
            if field_name in ['inventory', 'credential']:
                if not user.can_access(item.__class__, 'use', item):
                    continue
            if field_name in ['unified_job_template']:
                if not user.can_access(item.__class__, 'start', item, validate_license=False):
                    continue
            create_kwargs[field_name] = item
        create_kwargs['workflow_job_template'] = workflow_job_template
        return self.__class__.objects.create(**create_kwargs)


class WorkflowJobNode(WorkflowNodeBase):
    job = models.OneToOneField(
        'UnifiedJob',
        related_name='unified_job_node',
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

    def get_absolute_url(self, request=None):
        return reverse('api:workflow_job_node_detail', kwargs={'pk': self.pk}, request=request)

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
            data.update(accepted_fields)  # missing fields are handled in the scheduler
        # build ancestor artifacts, save them to node model for later
        aa_dict = {}
        for parent_node in self.get_parent_nodes():
            aa_dict.update(parent_node.ancestor_artifacts)
            if parent_node.job and hasattr(parent_node.job, 'artifacts'):
                aa_dict.update(parent_node.job.artifacts)
        if aa_dict:
            self.ancestor_artifacts = aa_dict
            self.save(update_fields=['ancestor_artifacts'])
        password_dict = {}
        if '_ansible_no_log' in aa_dict:
            for key in aa_dict:
                if key != '_ansible_no_log':
                    password_dict[key] = REPLACE_STR
        workflow_job_survey_passwords = self.workflow_job.survey_passwords
        if workflow_job_survey_passwords:
            password_dict.update(workflow_job_survey_passwords)
        if password_dict:
            data['survey_passwords'] = password_dict
        # process extra_vars
        extra_vars = {}
        if aa_dict:
            functional_aa_dict = copy(aa_dict)
            functional_aa_dict.pop('_ansible_no_log', None)
            extra_vars.update(functional_aa_dict)
        # Workflow Job extra_vars higher precedence than ancestor artifacts
        if self.workflow_job and self.workflow_job.extra_vars:
            extra_vars.update(self.workflow_job.extra_vars_dict)
        if extra_vars:
            data['extra_vars'] = extra_vars
        # ensure that unified jobs created by WorkflowJobs are marked
        data['launch_type'] = 'workflow'
        return data


class WorkflowJobOptions(BaseModel):
    class Meta:
        abstract = True

    extra_vars = prevent_search(models.TextField(
        blank=True,
        default='',
    ))
    allow_simultaneous = models.BooleanField(
        default=False
    )

    extra_vars_dict = VarsDictProperty('extra_vars', True)

    @property
    def workflow_nodes(self):
        raise NotImplementedError()

    def _create_workflow_nodes(self, old_node_list, user=None):
        node_links = {}
        for old_node in old_node_list:
            if user:
                new_node = old_node.create_wfjt_node_copy(user, workflow_job_template=self)
            else:
                new_node = old_node.create_workflow_job_node(workflow_job=self)
            node_links[old_node.pk] = new_node
        return node_links

    def _inherit_node_relationships(self, old_node_list, node_links):
        for old_node in old_node_list:
            new_node = node_links[old_node.pk]
            for relationship in ['always_nodes', 'success_nodes', 'failure_nodes']:
                old_manager = getattr(old_node, relationship)
                for old_child_node in old_manager.all():
                    new_child_node = node_links[old_child_node.pk]
                    new_manager = getattr(new_node, relationship)
                    new_manager.add(new_child_node)

    def copy_nodes_from_original(self, original=None, user=None):
        old_node_list = original.workflow_nodes.prefetch_related('always_nodes', 'success_nodes', 'failure_nodes').all()
        node_links = self._create_workflow_nodes(old_node_list, user=user)
        self._inherit_node_relationships(old_node_list, node_links)

    def create_relaunch_workflow_job(self):
        new_workflow_job = self.copy_unified_job()
        new_workflow_job.copy_nodes_from_original(original=self)
        return new_workflow_job


class WorkflowJobTemplate(UnifiedJobTemplate, WorkflowJobOptions, SurveyJobTemplateMixin, ResourceMixin):

    SOFT_UNIQUE_TOGETHER = [('polymorphic_ctype', 'name', 'organization')]

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

    @property
    def workflow_nodes(self):
        return self.workflow_job_template_nodes

    @classmethod
    def _get_unified_job_class(cls):
        return WorkflowJob

    @classmethod
    def _get_unified_job_field_names(cls):
        return ['name', 'description', 'extra_vars', 'labels', 'survey_passwords',
                'schedule', 'launch_type', 'allow_simultaneous']

    @classmethod
    def _get_unified_jt_copy_names(cls):
        base_list = super(WorkflowJobTemplate, cls)._get_unified_jt_copy_names()
        base_list.remove('labels')
        return (base_list +
                ['survey_spec', 'survey_enabled', 'organization'])

    def get_absolute_url(self, request=None):
        return reverse('api:workflow_job_template_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def cache_timeout_blocked(self):
        # TODO: don't allow running of job template if same workflow template running
        return False

    @property
    def notification_templates(self):
        base_notification_templates = NotificationTemplate.objects.all()
        error_notification_templates = list(base_notification_templates
                                            .filter(unifiedjobtemplate_notification_templates_for_errors__in=[self]))
        success_notification_templates = list(base_notification_templates
                                              .filter(unifiedjobtemplate_notification_templates_for_success__in=[self]))
        any_notification_templates = list(base_notification_templates
                                          .filter(unifiedjobtemplate_notification_templates_for_any__in=[self]))
        return dict(error=list(error_notification_templates),
                    success=list(success_notification_templates),
                    any=list(any_notification_templates))

    def create_unified_job(self, **kwargs):
        workflow_job = super(WorkflowJobTemplate, self).create_unified_job(**kwargs)
        workflow_job.copy_nodes_from_original(original=self)
        return workflow_job

    def _accept_or_ignore_job_kwargs(self, extra_vars=None, **kwargs):
        # Only accept allowed survey variables
        ignored_fields = {}
        prompted_fields = {}
        prompted_fields['extra_vars'] = {}
        ignored_fields['extra_vars'] = {}
        extra_vars = parse_yaml_or_json(extra_vars)
        if self.survey_enabled and self.survey_spec:
            survey_vars = [question['variable'] for question in self.survey_spec.get('spec', [])]
            for key in extra_vars:
                if key in survey_vars:
                    prompted_fields['extra_vars'][key] = extra_vars[key]
                else:
                    ignored_fields['extra_vars'][key] = extra_vars[key]
        else:
            prompted_fields['extra_vars'] = extra_vars

        return prompted_fields, ignored_fields

    def can_start_without_user_input(self):
        '''Return whether WFJT can be launched without survey passwords.'''
        return not bool(
            self.variables_needed_to_start or
            self.node_templates_missing() or
            self.node_prompts_rejected())

    def node_templates_missing(self):
        return [node.pk for node in self.workflow_job_template_nodes.filter(
                unified_job_template__isnull=True).all()]

    def node_prompts_rejected(self):
        node_list = []
        for node in self.workflow_job_template_nodes.prefetch_related('unified_job_template').all():
            node_prompts_warnings = node.get_prompts_warnings()
            if node_prompts_warnings:
                node_list.append(node.pk)
        return node_list

    def user_copy(self, user):
        new_wfjt = self.copy_unified_jt()
        new_wfjt.copy_nodes_from_original(original=self, user=user)
        return new_wfjt


class WorkflowJob(UnifiedJob, WorkflowJobOptions, SurveyJobMixin, JobNotificationMixin):
    class Meta:
        app_label = 'main'
        ordering = ('id',)

    workflow_job_template = models.ForeignKey(
        'WorkflowJobTemplate',
        related_name='workflow_jobs',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    @property
    def workflow_nodes(self):
        return self.workflow_job_nodes

    @classmethod
    def _get_parent_field_name(cls):
        return 'workflow_job_template'

    @classmethod
    def _get_unified_job_template_class(cls):
        return WorkflowJobTemplate

    def _has_failed(self):
        return False

    def socketio_emit_data(self):
        return {}

    def get_absolute_url(self, request=None):
        return reverse('api:workflow_job_detail', kwargs={'pk': self.pk}, request=request)

    def get_ui_url(self):
        return urljoin(settings.TOWER_URL_BASE, '/#/workflows/{}'.format(self.pk))

    def notification_data(self):
        result = super(WorkflowJob, self).notification_data()
        str_arr = ['Workflow job summary:', '']
        for node in self.workflow_job_nodes.all().select_related('job'):
            if node.job is None:
                node_job_description = 'no job.'
            else:
                node_job_description = ('job #{0}, "{1}", which finished with status {2}.'
                                        .format(node.job.id, node.job.name, node.job.status))
            str_arr.append("- node #{0} spawns {1}".format(node.id, node_job_description))
        result['body'] = '\n'.join(str_arr)
        return result

    @property
    def task_impact(self):
        return 0

    def get_notification_templates(self):
        return self.workflow_job_template.notification_templates

    def get_notification_friendly_name(self):
        return "Workflow Job"

    @property
    def preferred_instance_groups(self):
        return self.global_instance_groups

    '''
    A WorkflowJob is a virtual job. It doesn't result in a celery task.
    '''
    def start_celery_task(self, opts, error_callback, success_callback, queue):
        return None

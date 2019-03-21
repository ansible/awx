# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
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
from awx.main.fields import ImplicitRoleField, AskForField
from awx.main.models.mixins import (
    ResourceMixin,
    SurveyJobTemplateMixin,
    SurveyJobMixin,
    RelatedJobsMixin,
)
from awx.main.models.jobs import LaunchTimeConfigBase, LaunchTimeConfig, JobTemplate
from awx.main.models.credential import Credential
from awx.main.redact import REPLACE_STR
from awx.main.fields import JSONField

from copy import copy
from urllib.parse import urljoin

__all__ = ['WorkflowJobTemplate', 'WorkflowJob', 'WorkflowJobOptions', 'WorkflowJobNode', 'WorkflowJobTemplateNode',]


logger = logging.getLogger('awx.main.models.workflow')


class WorkflowNodeBase(CreatedModifiedModel, LaunchTimeConfig):
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

    def get_parent_nodes(self):
        '''Returns queryset containing all parents of this node'''
        success_parents = getattr(self, '%ss_success' % self.__class__.__name__.lower()).all()
        failure_parents = getattr(self, '%ss_failure' % self.__class__.__name__.lower()).all()
        always_parents = getattr(self, '%ss_always' % self.__class__.__name__.lower()).all()
        return (success_parents | failure_parents | always_parents).order_by('id')

    @classmethod
    def _get_workflow_job_field_names(cls):
        '''
        Return field names that should be copied from template node to job node.
        '''
        return ['workflow_job', 'unified_job_template',
                'extra_data', 'survey_passwords',
                'inventory', 'credentials', 'char_prompts']

    def create_workflow_job_node(self, **kwargs):
        '''
        Create a new workflow job node based on this workflow node.
        '''
        create_kwargs = {}
        for field_name in self._get_workflow_job_field_names():
            if field_name == 'credentials':
                continue
            if field_name in kwargs:
                create_kwargs[field_name] = kwargs[field_name]
            elif hasattr(self, field_name):
                create_kwargs[field_name] = getattr(self, field_name)
        new_node = WorkflowJobNode.objects.create(**create_kwargs)
        if self.pk:
            allowed_creds = self.credentials.all()
        else:
            allowed_creds = []
        for cred in allowed_creds:
            new_node.credentials.add(cred)
        return new_node


class WorkflowJobTemplateNode(WorkflowNodeBase):
    FIELDS_TO_PRESERVE_AT_COPY = [
        'unified_job_template', 'workflow_job_template', 'success_nodes', 'failure_nodes',
        'always_nodes', 'credentials', 'inventory', 'extra_data', 'survey_passwords',
        'char_prompts'
    ]
    REENCRYPTION_BLACKLIST_AT_COPY = ['extra_data', 'survey_passwords']

    workflow_job_template = models.ForeignKey(
        'WorkflowJobTemplate',
        related_name='workflow_job_template_nodes',
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
        allowed_creds = []
        for field_name in self._get_workflow_job_field_names():
            if field_name == 'credentials':
                for cred in self.credentials.all():
                    if user.can_access(Credential, 'use', cred):
                        allowed_creds.append(cred)
                continue
            item = getattr(self, field_name, None)
            if item is None:
                continue
            if field_name == 'inventory':
                if not user.can_access(item.__class__, 'use', item):
                    continue
            if field_name in ['unified_job_template']:
                if not user.can_access(item.__class__, 'start', item, validate_license=False):
                    continue
            create_kwargs[field_name] = item
        create_kwargs['workflow_job_template'] = workflow_job_template
        new_node = self.__class__.objects.create(**create_kwargs)
        for cred in allowed_creds:
            new_node.credentials.add(cred)
        return new_node


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
    do_not_run = models.BooleanField(
        default=False,
        help_text=_("Indidcates that a job will not be created when True. Workflow runtime "
                    "semantics will mark this True if the node is in a path that will "
                    "decidedly not be ran. A value of False means the node may not run."),
    )

    def get_absolute_url(self, request=None):
        return reverse('api:workflow_job_node_detail', kwargs={'pk': self.pk}, request=request)

    def prompts_dict(self, *args, **kwargs):
        r = super(WorkflowJobNode, self).prompts_dict(*args, **kwargs)
        # Explanation - WFJT extra_vars still break pattern, so they are not
        # put through prompts processing, but inventory is only accepted
        # if JT prompts for it, so it goes through this mechanism
        if self.workflow_job and self.workflow_job.inventory_id:
            # workflow job inventory takes precedence
            r['inventory'] = self.workflow_job.inventory
        return r

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
        if ujt_obj is not None:
            # MERGE note: move this to prompts_dict method on node when merging
            # with the workflow inventory branch
            prompts_data = self.prompts_dict()
            if isinstance(ujt_obj, WorkflowJobTemplate):
                if self.workflow_job.extra_vars:
                    prompts_data.setdefault('extra_vars', {})
                    prompts_data['extra_vars'].update(self.workflow_job.extra_vars_dict)
            accepted_fields, ignored_fields, errors = ujt_obj._accept_or_ignore_job_kwargs(**prompts_data)
            if errors:
                logger.info(_('Bad launch configuration starting template {template_pk} as part of '
                              'workflow {workflow_pk}. Errors:\n{error_text}').format(
                                  template_pk=ujt_obj.pk,
                                  workflow_pk=self.pk,
                                  error_text=errors))
            data.update(accepted_fields)  # missing fields are handled in the scheduler
            try:
                # config saved on the workflow job itself
                wj_config = self.workflow_job.launch_config
            except ObjectDoesNotExist:
                wj_config = None
            if wj_config:
                accepted_fields, ignored_fields, errors = ujt_obj._accept_or_ignore_job_kwargs(**wj_config.prompts_dict())
                accepted_fields.pop('extra_vars', None)  # merge handled with other extra_vars later
                data.update(accepted_fields)
        # build ancestor artifacts, save them to node model for later
        aa_dict = {}
        is_root_node = True
        for parent_node in self.get_parent_nodes():
            is_root_node = False
            aa_dict.update(parent_node.ancestor_artifacts)
            if parent_node.job and hasattr(parent_node.job, 'artifacts'):
                aa_dict.update(parent_node.job.artifacts)
        if aa_dict and not is_root_node:
            self.ancestor_artifacts = aa_dict
            self.save(update_fields=['ancestor_artifacts'])
        # process password list
        password_dict = {}
        if '_ansible_no_log' in aa_dict:
            for key in aa_dict:
                if key != '_ansible_no_log':
                    password_dict[key] = REPLACE_STR
        if self.workflow_job.survey_passwords:
            password_dict.update(self.workflow_job.survey_passwords)
        if self.survey_passwords:
            password_dict.update(self.survey_passwords)
        if password_dict:
            data['survey_passwords'] = password_dict
        # process extra_vars
        extra_vars = data.get('extra_vars', {})
        if ujt_obj and isinstance(ujt_obj, (JobTemplate, WorkflowJobTemplate)):
            if aa_dict:
                functional_aa_dict = copy(aa_dict)
                functional_aa_dict.pop('_ansible_no_log', None)
                extra_vars.update(functional_aa_dict)
        if ujt_obj and isinstance(ujt_obj, JobTemplate):
            # Workflow Job extra_vars higher precedence than ancestor artifacts
            if self.workflow_job and self.workflow_job.extra_vars:
                extra_vars.update(self.workflow_job.extra_vars_dict)
        if extra_vars:
            data['extra_vars'] = extra_vars
        # ensure that unified jobs created by WorkflowJobs are marked
        data['_eager_fields'] = {'launch_type': 'workflow'}
        if self.workflow_job and self.workflow_job.created_by:
            data['_eager_fields']['created_by'] = self.workflow_job.created_by
        # Extra processing in the case that this is a slice job
        if 'job_slice' in self.ancestor_artifacts and is_root_node:
            data['_eager_fields']['allow_simultaneous'] = True
            data['_eager_fields']['job_slice_number'] = self.ancestor_artifacts['job_slice']
            data['_eager_fields']['job_slice_count'] = self.workflow_job.workflow_job_nodes.count()
            data['_prevent_slicing'] = True
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

    @classmethod
    def _get_unified_job_field_names(cls):
        return set(f.name for f in WorkflowJobOptions._meta.fields) | set(
            # NOTE: if other prompts are added to WFJT, put fields in WJOptions, remove inventory
            ['name', 'description', 'schedule', 'survey_passwords', 'labels', 'inventory']
        )

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
        if self.unified_job_template_id is None:
            new_workflow_job.copy_nodes_from_original(original=self)
        return new_workflow_job


class WorkflowJobTemplate(UnifiedJobTemplate, WorkflowJobOptions, SurveyJobTemplateMixin, ResourceMixin, RelatedJobsMixin):

    SOFT_UNIQUE_TOGETHER = [('polymorphic_ctype', 'name', 'organization')]
    FIELDS_TO_PRESERVE_AT_COPY = [
        'labels', 'instance_groups', 'workflow_job_template_nodes', 'credentials', 'survey_spec'
    ]

    class Meta:
        app_label = 'main'

    organization = models.ForeignKey(
        'Organization',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='workflows',
    )
    inventory = models.ForeignKey(
        'Inventory',
        related_name='%(class)ss',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        help_text=_('Inventory applied to all job templates in workflow that prompt for inventory.'),
    )
    ask_inventory_on_launch = AskForField(
        blank=True,
        default=False,
    )
    admin_role = ImplicitRoleField(parent_role=[
        'singleton:' + ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
        'organization.workflow_admin_role'
    ])
    execute_role = ImplicitRoleField(parent_role=[
        'admin_role',
        'organization.execute_role',
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
    def _get_unified_jt_copy_names(cls):
        base_list = super(WorkflowJobTemplate, cls)._get_unified_jt_copy_names()
        base_list.remove('labels')
        return (base_list |
                set(['survey_spec', 'survey_enabled', 'ask_variables_on_launch', 'organization']))

    def get_absolute_url(self, request=None):
        return reverse('api:workflow_job_template_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def cache_timeout_blocked(self):
        if WorkflowJob.objects.filter(workflow_job_template=self,
                                      status__in=['pending', 'waiting', 'running']).count() >= getattr(settings, 'SCHEDULE_MAX_JOBS', 10):
            logger.error("Workflow Job template %s could not be started because there are more than %s other jobs from that template waiting to run" %
                         (self.name, getattr(settings, 'SCHEDULE_MAX_JOBS', 10)))
            return True
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

    def _accept_or_ignore_job_kwargs(self, **kwargs):
        exclude_errors = kwargs.pop('_exclude_errors', [])
        prompted_data = {}
        rejected_data = {}
        errors_dict = {}

        # Handle all the fields that have prompting rules
        # NOTE: If WFJTs prompt for other things, this logic can be combined with jobs
        for field_name, ask_field_name in self.get_ask_mapping().items():

            if field_name == 'extra_vars':
                accepted_vars, rejected_vars, vars_errors = self.accept_or_ignore_variables(
                    kwargs.get('extra_vars', {}),
                    _exclude_errors=exclude_errors,
                    extra_passwords=kwargs.get('survey_passwords', {}))
                if accepted_vars:
                    prompted_data['extra_vars'] = accepted_vars
                if rejected_vars:
                    rejected_data['extra_vars'] = rejected_vars
                errors_dict.update(vars_errors)
                continue

            if field_name not in kwargs:
                continue
            new_value = kwargs[field_name]
            old_value = getattr(self, field_name)

            if new_value == old_value:
                continue  # no-op case: Counted as neither accepted or ignored
            elif getattr(self, ask_field_name):
                # accepted prompt
                prompted_data[field_name] = new_value
            else:
                # unprompted - template is not configured to accept field on launch
                rejected_data[field_name] = new_value
                # Not considered an error for manual launch, to support old
                # behavior of putting them in ignored_fields and launching anyway
                if 'prompts' not in exclude_errors:
                    errors_dict[field_name] = _('Field is not configured to prompt on launch.').format(field_name=field_name)

        return prompted_data, rejected_data, errors_dict

    def can_start_without_user_input(self):
        return not bool(self.variables_needed_to_start)

    def node_templates_missing(self):
        return [node.pk for node in self.workflow_job_template_nodes.filter(
                unified_job_template__isnull=True).all()]

    def node_prompts_rejected(self):
        node_list = []
        for node in self.workflow_job_template_nodes.prefetch_related('unified_job_template').all():
            ujt_obj = node.unified_job_template
            if ujt_obj is None:
                continue
            prompts_dict = node.prompts_dict()
            accepted_fields, ignored_fields, prompts_errors = ujt_obj._accept_or_ignore_job_kwargs(**prompts_dict)
            if prompts_errors:
                node_list.append(node.pk)
        return node_list

    '''
    RelatedJobsMixin
    '''
    def _get_related_jobs(self):
        return WorkflowJob.objects.filter(workflow_job_template=self)


class WorkflowJob(UnifiedJob, WorkflowJobOptions, SurveyJobMixin, JobNotificationMixin, LaunchTimeConfigBase):
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
    job_template = models.ForeignKey(
        'JobTemplate',
        related_name='slice_workflow_jobs',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        help_text=_("If automatically created for a sliced job run, the job template "
                    "the workflow job was created from."),
    )
    is_sliced_job = models.BooleanField(
        default=False
    )

    @property
    def workflow_nodes(self):
        return self.workflow_job_nodes

    def _get_parent_field_name(self):
        if self.job_template_id:
            # This is a workflow job which is a container for slice jobs
            return 'job_template'
        return 'workflow_job_template'

    @classmethod
    def _get_unified_job_template_class(cls):
        return WorkflowJobTemplate

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

    def get_ancestor_workflows(self):
        """Returns a list of WFJTs that are indirect parents of this workflow job
        say WFJTs are set up to spawn in order of A->B->C, and this workflow job
        came from C, then C is the parent and [B, A] will be returned from this.
        """
        ancestors = []
        wj_ids = set([self.pk])
        wj = self.get_workflow_job()
        while wj and wj.workflow_job_template_id:
            if wj.pk in wj_ids:
                logger.critical('Cycles detected in the workflow jobs graph, '
                                'this is not normal and suggests task manager degeneracy.')
                break
            wj_ids.add(wj.pk)
            ancestors.append(wj.workflow_job_template)
            wj = wj.get_workflow_job()
        return ancestors

    def get_notification_templates(self):
        return self.workflow_job_template.notification_templates

    def get_notification_friendly_name(self):
        return "Workflow Job"

    @property
    def preferred_instance_groups(self):
        return []

    @property
    def actually_running(self):
        # WorkflowJobs don't _actually_ run anything in the dispatcher, so
        # there's no point in asking the dispatcher if it knows about this task
        return self.status == 'running'

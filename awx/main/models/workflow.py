# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
import json
import logging
from uuid import uuid4
from copy import copy
from urllib.parse import urljoin

# Django
from django.db import connection, models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
#from django import settings as tower_settings

# Django-CRUM
from crum import get_current_user

from jinja2 import sandbox
from jinja2.exceptions import TemplateSyntaxError, UndefinedError, SecurityError

# AWX
from awx.api.versioning import reverse
from awx.main.models import (prevent_search, accepts_json, UnifiedJobTemplate,
                             UnifiedJob)
from awx.main.models.notifications import (
    NotificationTemplate,
    JobNotificationMixin
)
from awx.main.models.base import CreatedModifiedModel, VarsDictProperty
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
    WebhookMixin,
    WebhookTemplateMixin,
)
from awx.main.models.jobs import LaunchTimeConfigBase, LaunchTimeConfig, JobTemplate
from awx.main.models.credential import Credential
from awx.main.redact import REPLACE_STR
from awx.main.fields import JSONField
from awx.main.utils import schedule_task_manager


__all__ = ['WorkflowJobTemplate', 'WorkflowJob', 'WorkflowJobOptions', 'WorkflowJobNode',
           'WorkflowJobTemplateNode', 'WorkflowApprovalTemplate', 'WorkflowApproval']


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
    all_parents_must_converge = models.BooleanField(
        default=False,
        help_text=_("If enabled then the node will only run if all of the parent nodes "
                    "have met the criteria to reach this node")
    )
    unified_job_template = models.ForeignKey(
        'UnifiedJobTemplate',
        related_name='%(class)ss',
        blank=True,
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
                'inventory', 'credentials', 'char_prompts', 'all_parents_must_converge']

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
        create_kwargs['identifier'] = self.identifier
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
        'char_prompts', 'all_parents_must_converge', 'identifier'
    ]
    REENCRYPTION_BLOCKLIST_AT_COPY = ['extra_data', 'survey_passwords']

    workflow_job_template = models.ForeignKey(
        'WorkflowJobTemplate',
        related_name='workflow_job_template_nodes',
        on_delete=models.CASCADE,
    )
    identifier = models.CharField(
        max_length=512,
        default=uuid4,
        blank=False,
        help_text=_(
            'An identifier for this node that is unique within its workflow. '
            'It is copied to workflow job nodes corresponding to this node.'),
    )

    class Meta:
        app_label = 'main'
        unique_together = (("identifier", "workflow_job_template"),)
        indexes = [
            models.Index(fields=['identifier']),
        ]

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

    def create_approval_template(self, **kwargs):
        approval_template = WorkflowApprovalTemplate(**kwargs)
        approval_template.save()
        self.unified_job_template = approval_template
        self.save()
        return approval_template


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
        default=dict,
        editable=False,
    )
    do_not_run = models.BooleanField(
        default=False,
        help_text=_("Indicates that a job will not be created when True. Workflow runtime "
                    "semantics will mark this True if the node is in a path that will "
                    "decidedly not be ran. A value of False means the node may not run."),
    )
    identifier = models.CharField(
        max_length=512,
        blank=True,  # blank denotes pre-migration job nodes
        help_text=_('An identifier coresponding to the workflow job template node that this node was created from.'),
    )

    class Meta:
        app_label = 'main'
        indexes = [
            models.Index(fields=["identifier", "workflow_job"]),
            models.Index(fields=['identifier']),
        ]

    def get_absolute_url(self, request=None):
        return reverse('api:workflow_job_node_detail', kwargs={'pk': self.pk}, request=request)

    def prompts_dict(self, *args, **kwargs):
        r = super(WorkflowJobNode, self).prompts_dict(*args, **kwargs)
        # Explanation - WFJT extra_vars still break pattern, so they are not
        # put through prompts processing, but inventory and others are only accepted
        # if JT prompts for it, so it goes through this mechanism
        if self.workflow_job:
            if self.workflow_job.inventory_id:
                # workflow job inventory takes precedence
                r['inventory'] = self.workflow_job.inventory
            if self.workflow_job.char_prompts:
                r.update(self.workflow_job.char_prompts)
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


class WorkflowJobOptions(LaunchTimeConfigBase):
    class Meta:
        abstract = True

    extra_vars = accepts_json(prevent_search(models.TextField(
        blank=True,
        default='',
    )))
    allow_simultaneous = models.BooleanField(
        default=False
    )

    extra_vars_dict = VarsDictProperty('extra_vars', True)

    @property
    def workflow_nodes(self):
        raise NotImplementedError()

    @classmethod
    def _get_unified_job_field_names(cls):
        r = set(f.name for f in WorkflowJobOptions._meta.fields) | set(
            ['name', 'description', 'organization', 'survey_passwords', 'labels', 'limit', 'scm_branch']
        )
        r.remove('char_prompts')  # needed due to copying launch config to launch config
        return r

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


class WorkflowJobTemplate(UnifiedJobTemplate, WorkflowJobOptions, SurveyJobTemplateMixin, ResourceMixin, RelatedJobsMixin, WebhookTemplateMixin):

    SOFT_UNIQUE_TOGETHER = [('polymorphic_ctype', 'name', 'organization')]
    FIELDS_TO_PRESERVE_AT_COPY = [
        'labels', 'organization', 'instance_groups', 'workflow_job_template_nodes', 'credentials', 'survey_spec'
    ]

    class Meta:
        app_label = 'main'

    ask_inventory_on_launch = AskForField(
        blank=True,
        default=False,
    )
    ask_limit_on_launch = AskForField(
        blank=True,
        default=False,
    )
    ask_scm_branch_on_launch = AskForField(
        blank=True,
        default=False,
    )
    notification_templates_approvals = models.ManyToManyField(
        "NotificationTemplate",
        blank=True,
        related_name='%(class)s_notification_templates_for_approvals'
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
        'organization.auditor_role', 'execute_role', 'admin_role',
        'approval_role',
    ])
    approval_role = ImplicitRoleField(parent_role=[
        'organization.approval_role', 'admin_role',
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
        started_notification_templates = list(base_notification_templates
                                              .filter(unifiedjobtemplate_notification_templates_for_started__in=[self]))
        success_notification_templates = list(base_notification_templates
                                              .filter(unifiedjobtemplate_notification_templates_for_success__in=[self]))
        approval_notification_templates = list(base_notification_templates
                                               .filter(workflowjobtemplate_notification_templates_for_approvals__in=[self]))
        # Get Organization NotificationTemplates
        if self.organization is not None:
            error_notification_templates = set(error_notification_templates + list(base_notification_templates.filter(
                organization_notification_templates_for_errors=self.organization)))
            started_notification_templates = set(started_notification_templates + list(base_notification_templates.filter(
                organization_notification_templates_for_started=self.organization)))
            success_notification_templates = set(success_notification_templates + list(base_notification_templates.filter(
                organization_notification_templates_for_success=self.organization)))
            approval_notification_templates = set(approval_notification_templates + list(base_notification_templates.filter(
                organization_notification_templates_for_approvals=self.organization)))
        return dict(error=list(error_notification_templates),
                    started=list(started_notification_templates),
                    success=list(success_notification_templates),
                    approvals=list(approval_notification_templates))

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


class WorkflowJob(UnifiedJob, WorkflowJobOptions, SurveyJobMixin, JobNotificationMixin, WebhookMixin):
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


class WorkflowApprovalTemplate(UnifiedJobTemplate):

    FIELDS_TO_PRESERVE_AT_COPY = ['description', 'timeout',]

    class Meta:
        app_label = 'main'

    timeout = models.IntegerField(
        blank=True,
        default=0,
        help_text=_("The amount of time (in seconds) before the approval node expires and fails."),
    )

    @classmethod
    def _get_unified_job_class(cls):
        return WorkflowApproval

    @classmethod
    def _get_unified_job_field_names(cls):
        return ['name', 'description', 'timeout']

    def get_absolute_url(self, request=None):
        return reverse('api:workflow_approval_template_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def workflow_job_template(self):
        return self.workflowjobtemplatenodes.first().workflow_job_template


class WorkflowApproval(UnifiedJob, JobNotificationMixin):
    class Meta:
        app_label = 'main'

    workflow_approval_template = models.ForeignKey(
        'WorkflowApprovalTemplate',
        related_name='approvals',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    timeout = models.IntegerField(
        blank=True,
        default=0,
        help_text=_("The amount of time (in seconds) before the approval node expires and fails."),
    )
    timed_out = models.BooleanField(
        default=False,
        help_text=_("Shows when an approval node (with a timeout assigned to it) has timed out.")
    )
    approved_or_denied_by = models.ForeignKey(
        'auth.User',
        related_name='%s(class)s_approved+',
        default=None,
        null=True,
        editable=False,
        on_delete=models.SET_NULL,
    )


    @classmethod
    def _get_unified_job_template_class(cls):
        return WorkflowApprovalTemplate

    def get_absolute_url(self, request=None):
        return reverse('api:workflow_approval_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def event_class(self):
        return None

    def get_ui_url(self):
        return urljoin(settings.TOWER_URL_BASE, '/#/workflows/{}'.format(self.workflow_job.id))

    def _get_parent_field_name(self):
        return 'workflow_approval_template'

    def approve(self, request=None):
        self.status = 'successful'
        self.approved_or_denied_by = get_current_user()
        self.save()
        self.send_approval_notification('approved')
        self.websocket_emit_status(self.status)
        schedule_task_manager()
        return reverse('api:workflow_approval_approve', kwargs={'pk': self.pk}, request=request)

    def deny(self, request=None):
        self.status = 'failed'
        self.approved_or_denied_by = get_current_user()
        self.save()
        self.send_approval_notification('denied')
        self.websocket_emit_status(self.status)
        schedule_task_manager()
        return reverse('api:workflow_approval_deny', kwargs={'pk': self.pk}, request=request)

    def signal_start(self, **kwargs):
        can_start = super(WorkflowApproval, self).signal_start(**kwargs)
        self.started = self.created
        self.save(update_fields=['started'])
        self.send_approval_notification('running')
        return can_start

    @property
    def event_processing_finished(self):
        return True

    def send_approval_notification(self, approval_status):
        from awx.main.tasks import send_notifications  # avoid circular import
        if self.workflow_job_template is None:
            return
        for nt in self.workflow_job_template.notification_templates["approvals"]:
            try:
                (notification_subject, notification_body) = self.build_approval_notification_message(nt, approval_status)
            except Exception:
                raise NotImplementedError("build_approval_notification_message() does not exist")

            # Use kwargs to force late-binding
            # https://stackoverflow.com/a/3431699/10669572
            def send_it(local_nt=nt, local_subject=notification_subject, local_body=notification_body):
                def _func():
                    send_notifications.delay([local_nt.generate_notification(local_subject, local_body).id],
                                             job_id=self.id)
                return _func
            connection.on_commit(send_it())

    def build_approval_notification_message(self, nt, approval_status):
        env = sandbox.ImmutableSandboxedEnvironment()

        context = self.context(approval_status)

        msg_template = body_template = None
        msg = body = ''

        # Use custom template if available
        if nt.messages and nt.messages.get('workflow_approval', None):
            template = nt.messages['workflow_approval'].get(approval_status, {})
            msg_template = template.get('message', None)
            body_template = template.get('body', None)
        # If custom template not provided, look up default template
        default_template = nt.notification_class.default_messages['workflow_approval'][approval_status]
        if not msg_template:
            msg_template = default_template.get('message', None)
        if not body_template:
            body_template = default_template.get('body', None)

        if msg_template:
            try:
                msg = env.from_string(msg_template).render(**context)
            except (TemplateSyntaxError, UndefinedError, SecurityError):
                msg = ''

        if body_template:
            try:
                body = env.from_string(body_template).render(**context)
            except (TemplateSyntaxError, UndefinedError, SecurityError):
                body = ''

        return (msg, body)

    def context(self, approval_status):
        workflow_url = urljoin(settings.TOWER_URL_BASE, '/#/workflows/{}'.format(self.workflow_job.id))
        return {'approval_status': approval_status,
                'approval_node_name': self.workflow_approval_template.name,
                'workflow_url': workflow_url,
                'job_metadata': json.dumps(self.notification_data(), indent=4)}

    @property
    def workflow_job_template(self):
        try:
            return self.unified_job_node.workflow_job.unified_job_template
        except ObjectDoesNotExist:
            return None

    @property
    def workflow_job(self):
        return self.unified_job_node.workflow_job

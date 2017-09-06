# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import datetime
import hashlib
import hmac
import logging
import time
import json
import base64
from urlparse import urljoin

# Django
from django.conf import settings
from django.db import models
#from django.core.cache import cache
import memcache
from django.db.models import Q, Count
from django.utils.dateparse import parse_datetime
from dateutil import parser
from dateutil.tz import tzutc
from django.utils.encoding import force_text, smart_str
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

# AWX
from awx.api.versioning import reverse
from awx.main.models.base import * # noqa
from awx.main.models.unified_jobs import * # noqa
from awx.main.models.notifications import (
    NotificationTemplate,
    JobNotificationMixin,
)
from awx.main.utils import (
    ignore_inventory_computed_fields,
    parse_yaml_or_json,
)
from awx.main.fields import ImplicitRoleField
from awx.main.models.mixins import ResourceMixin, SurveyJobTemplateMixin, SurveyJobMixin, TaskManagerJobMixin
from awx.main.models.base import PERM_INVENTORY_SCAN
from awx.main.fields import JSONField

from awx.main.consumers import emit_channel_notification


logger = logging.getLogger('awx.main.models.jobs')
analytics_logger = logging.getLogger('awx.analytics.job_events')
system_tracking_logger = logging.getLogger('awx.analytics.system_tracking')

__all__ = ['JobTemplate', 'Job', 'JobHostSummary', 'JobEvent', 'SystemJobOptions', 'SystemJobTemplate', 'SystemJob']


class JobOptions(BaseModel):
    '''
    Common options for job templates and jobs.
    '''

    class Meta:
        abstract = True

    diff_mode = models.BooleanField(
        default=False,
        help_text=_("If enabled, textual changes made to any templated files on the host are shown in the standard output"),
    )
    job_type = models.CharField(
        max_length=64,
        choices=JOB_TYPE_CHOICES,
        default='run',
    )
    inventory = models.ForeignKey(
        'Inventory',
        related_name='%(class)ss',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    project = models.ForeignKey(
        'Project',
        related_name='%(class)ss',
        null=True,
        default=None,
        blank=True,
        on_delete=models.SET_NULL,
    )
    playbook = models.CharField(
        max_length=1024,
        default='',
        blank=True,
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='%(class)ss',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    vault_credential = models.ForeignKey(
        'Credential',
        related_name='%(class)ss_as_vault_credential+',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    extra_credentials = models.ManyToManyField(
        'Credential',
        related_name='%(class)ss_as_extra_credential+',
    )
    forks = models.PositiveIntegerField(
        blank=True,
        default=0,
    )
    limit = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    verbosity = models.PositiveIntegerField(
        choices=VERBOSITY_CHOICES,
        blank=True,
        default=0,
    )
    extra_vars = prevent_search(models.TextField(
        blank=True,
        default='',
    ))
    job_tags = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    force_handlers = models.BooleanField(
        blank=True,
        default=False,
    )
    skip_tags = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    start_at_task = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    become_enabled = models.BooleanField(
        default=False,
    )
    allow_simultaneous = models.BooleanField(
        default=False,
    )
    timeout = models.IntegerField(
        blank=True,
        default=0,
        help_text=_("The amount of time (in seconds) to run before the task is canceled."),
    )
    use_fact_cache = models.BooleanField(
        default=False,
        help_text=_("If enabled, Tower will act as an Ansible Fact Cache Plugin; persisting facts at the end of a playbook run to the database and caching facts for use by Ansible."),
    )

    extra_vars_dict = VarsDictProperty('extra_vars', True)

    def clean_credential(self):
        cred = self.credential
        if cred and cred.kind != 'ssh':
            raise ValidationError(
                _('You must provide an SSH credential.'),
            )
        return cred

    def clean_vault_credential(self):
        cred = self.vault_credential
        if cred and cred.kind != 'vault':
            raise ValidationError(
                _('You must provide a Vault credential.'),
            )
        return cred

    @property
    def all_credentials(self):
        credentials = list(self.extra_credentials.all())
        if self.vault_credential:
            credentials.insert(0, self.vault_credential)
        if self.credential:
            credentials.insert(0, self.credential)
        return credentials

    @property
    def network_credentials(self):
        return [cred for cred in self.extra_credentials.all() if cred.credential_type.kind == 'net']

    @property
    def cloud_credentials(self):
        return [cred for cred in self.extra_credentials.all() if cred.credential_type.kind == 'cloud']

    # TODO: remove when API v1 is removed
    @property
    def cloud_credential(self):
        try:
            return self.cloud_credentials[-1].pk
        except IndexError:
            return None

    # TODO: remove when API v1 is removed
    @property
    def network_credential(self):
        try:
            return self.network_credentials[-1].pk
        except IndexError:
            return None

    @property
    def passwords_needed_to_start(self):
        '''Return list of password field names needed to start the job.'''
        needed = []
        if self.credential:
            needed.extend(self.credential.passwords_needed)
        if self.vault_credential:
            needed.extend(self.vault_credential.passwords_needed)
        return needed


class JobTemplate(UnifiedJobTemplate, JobOptions, SurveyJobTemplateMixin, ResourceMixin):
    '''
    A job template is a reusable job definition for applying a project (with
    playbook) to an inventory source with a given credential.
    '''
    SOFT_UNIQUE_TOGETHER = [('polymorphic_ctype', 'name')]

    class Meta:
        app_label = 'main'
        ordering = ('name',)

    host_config_key = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    ask_diff_mode_on_launch = models.BooleanField(
        blank=True,
        default=False,
    )
    ask_variables_on_launch = models.BooleanField(
        blank=True,
        default=False,
    )
    ask_limit_on_launch = models.BooleanField(
        blank=True,
        default=False,
    )
    ask_tags_on_launch = models.BooleanField(
        blank=True,
        default=False,
    )
    ask_skip_tags_on_launch = models.BooleanField(
        blank=True,
        default=False,
    )
    ask_job_type_on_launch = models.BooleanField(
        blank=True,
        default=False,
    )
    ask_verbosity_on_launch = models.BooleanField(
        blank=True,
        default=False,
    )
    ask_inventory_on_launch = models.BooleanField(
        blank=True,
        default=False,
    )
    ask_credential_on_launch = models.BooleanField(
        blank=True,
        default=False,
    )
    admin_role = ImplicitRoleField(
        parent_role=['project.organization.admin_role', 'inventory.organization.admin_role']
    )
    execute_role = ImplicitRoleField(
        parent_role=['admin_role'],
    )
    read_role = ImplicitRoleField(
        parent_role=['project.organization.auditor_role', 'inventory.organization.auditor_role', 'execute_role', 'admin_role'],
    )


    @classmethod
    def _get_unified_job_class(cls):
        return Job

    @classmethod
    def _get_unified_job_field_names(cls):
        return ['name', 'description', 'job_type', 'inventory', 'project',
                'playbook', 'credential', 'vault_credential',
                'extra_credentials', 'forks', 'schedule', 'limit', 'verbosity',
                'job_tags', 'extra_vars', 'launch_type', 'force_handlers',
                'skip_tags', 'start_at_task', 'become_enabled', 'labels',
                'survey_passwords', 'allow_simultaneous', 'timeout',
                'use_fact_cache', 'diff_mode',]

    def resource_validation_data(self):
        '''
        Process consistency errors and need-for-launch related fields.
        '''
        resources_needed_to_start = []
        validation_errors = {}

        # Inventory and Credential related checks
        if self.inventory is None:
            resources_needed_to_start.append('inventory')
            if not self.ask_inventory_on_launch:
                validation_errors['inventory'] = [_("Job Template must provide 'inventory' or allow prompting for it."),]
        if self.credential is None and self.vault_credential is None:
            resources_needed_to_start.append('credential')
            if not self.ask_credential_on_launch:
                validation_errors['credential'] = [_("Job Template must provide 'credential' or allow prompting for it."),]

        # Job type dependent checks
        if self.project is None:
            resources_needed_to_start.append('project')
            validation_errors['project'] = [_("Job types 'run' and 'check' must have assigned a project."),]

        return (validation_errors, resources_needed_to_start)

    @property
    def resources_needed_to_start(self):
        validation_errors, resources_needed_to_start = self.resource_validation_data()
        return resources_needed_to_start

    def create_job(self, **kwargs):
        '''
        Create a new job based on this template.
        '''
        return self.create_unified_job(**kwargs)

    def get_absolute_url(self, request=None):
        return reverse('api:job_template_detail', kwargs={'pk': self.pk}, request=request)

    def can_start_without_user_input(self, callback_extra_vars=None):
        '''
        Return whether job template can be used to start a new job without
        requiring any user input.
        '''
        variables_needed = False
        if callback_extra_vars:
            extra_vars_dict = parse_yaml_or_json(callback_extra_vars)
            for var in self.variables_needed_to_start:
                if var not in extra_vars_dict:
                    variables_needed = True
                    break
        elif self.variables_needed_to_start:
            variables_needed = True
        prompting_needed = False
        # The behavior of provisioning callback should mimic
        # that of job template launch, so prompting_needed should
        # not block a provisioning callback from creating/launching jobs.
        if callback_extra_vars is None:
            for value in self._ask_for_vars_dict().values():
                if value:
                    prompting_needed = True
        return (not prompting_needed and
                not self.passwords_needed_to_start and
                not variables_needed)

    def _ask_for_vars_dict(self):
        return dict(
            diff_mode=self.ask_diff_mode_on_launch,
            extra_vars=self.ask_variables_on_launch,
            limit=self.ask_limit_on_launch,
            job_tags=self.ask_tags_on_launch,
            skip_tags=self.ask_skip_tags_on_launch,
            job_type=self.ask_job_type_on_launch,
            verbosity=self.ask_verbosity_on_launch,
            inventory=self.ask_inventory_on_launch,
            credential=self.ask_credential_on_launch,
            vault_credential=self.ask_credential_on_launch,
            extra_credentials=self.ask_credential_on_launch,
        )

    def _accept_or_ignore_job_kwargs(self, **kwargs):
        # Sort the runtime fields allowed and disallowed by job template
        ignored_fields = {}
        prompted_fields = {}

        ask_for_vars_dict = self._ask_for_vars_dict()

        for field in ask_for_vars_dict:
            if field in kwargs:
                if field == 'extra_vars':
                    prompted_fields[field] = {}
                    ignored_fields[field] = {}
                if ask_for_vars_dict[field]:
                    prompted_fields[field] = kwargs[field]
                else:
                    if field == 'extra_vars' and self.survey_enabled and self.survey_spec:
                        # Accept vars defined in the survey and no others
                        survey_vars = [question['variable'] for question in self.survey_spec.get('spec', [])]
                        extra_vars = parse_yaml_or_json(kwargs[field])
                        for key in extra_vars:
                            if key in survey_vars:
                                prompted_fields[field][key] = extra_vars[key]
                            else:
                                ignored_fields[field][key] = extra_vars[key]
                    else:
                        ignored_fields[field] = kwargs[field]

        return prompted_fields, ignored_fields

    def _extra_job_type_errors(self, data):
        """
        Used to enforce 2 special cases around scan jobs and prompting
         - the inventory cannot be changed on a scan job template
         - scan jobs cannot be switched to run/check type and vice versa
        """
        errors = {}
        if 'job_type' in data and self.ask_job_type_on_launch:
            if data['job_type'] == PERM_INVENTORY_SCAN and not self.job_type == PERM_INVENTORY_SCAN:
                errors['job_type'] = _('Cannot override job_type to or from a scan job.')
        return errors

    @property
    def cache_timeout_blocked(self):
        if Job.objects.filter(job_template=self, status__in=['pending', 'waiting', 'running']).count() > getattr(settings, 'SCHEDULE_MAX_JOBS', 10):
            logger.error("Job template %s could not be started because there are more than %s other jobs from that template waiting to run" %
                         (self.name, getattr(settings, 'SCHEDULE_MAX_JOBS', 10)))
            return True
        return False

    def _can_update(self):
        return self.can_start_without_user_input()

    @property
    def notification_templates(self):
        # Return all notification_templates defined on the Job Template, on the Project, and on the Organization for each trigger type
        # TODO: Currently there is no org fk on project so this will need to be added once that is
        #       available after the rbac pr
        base_notification_templates = NotificationTemplate.objects
        error_notification_templates = list(base_notification_templates.filter(unifiedjobtemplate_notification_templates_for_errors__in=[self, self.project]))
        success_notification_templates = list(base_notification_templates.filter(unifiedjobtemplate_notification_templates_for_success__in=[self, self.project]))
        any_notification_templates = list(base_notification_templates.filter(unifiedjobtemplate_notification_templates_for_any__in=[self, self.project]))
        # Get Organization NotificationTemplates
        if self.project is not None and self.project.organization is not None:
            error_notification_templates = set(error_notification_templates + list(base_notification_templates.filter(organization_notification_templates_for_errors=self.project.organization)))
            success_notification_templates = set(success_notification_templates + list(base_notification_templates.filter(organization_notification_templates_for_success=self.project.organization)))
            any_notification_templates = set(any_notification_templates + list(base_notification_templates.filter(organization_notification_templates_for_any=self.project.organization)))
        return dict(error=list(error_notification_templates), success=list(success_notification_templates), any=list(any_notification_templates))


class Job(UnifiedJob, JobOptions, SurveyJobMixin, JobNotificationMixin, TaskManagerJobMixin):
    '''
    A job applies a project (with playbook) to an inventory source with a given
    credential.  It represents a single invocation of ansible-playbook with the
    given parameters.
    '''

    class Meta:
        app_label = 'main'
        ordering = ('id',)

    job_template = models.ForeignKey(
        'JobTemplate',
        related_name='jobs',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    hosts = models.ManyToManyField(
        'Host',
        related_name='jobs',
        editable=False,
        through='JobHostSummary',
    )
    artifacts = JSONField(
        blank=True,
        default={},
        editable=False,
    )
    scm_revision = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        editable=False,
        verbose_name=_('SCM Revision'),
        help_text=_('The SCM Revision from the Project used for this job, if available'),
    )
    project_update = models.ForeignKey(
        'ProjectUpdate',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        help_text=_('The SCM Refresh task used to make sure the playbooks were available for the job run'),
    )


    @classmethod
    def _get_parent_field_name(cls):
        return 'job_template'

    @classmethod
    def _get_task_class(cls):
        from awx.main.tasks import RunJob
        return RunJob

    @classmethod
    def supports_isolation(cls):
        return True

    def _global_timeout_setting(self):
        return 'DEFAULT_JOB_TIMEOUT'

    @classmethod
    def _get_unified_job_template_class(cls):
        return JobTemplate

    def get_absolute_url(self, request=None):
        return reverse('api:job_detail', kwargs={'pk': self.pk}, request=request)

    def get_ui_url(self):
        return urljoin(settings.TOWER_URL_BASE, "/#/jobs/{}".format(self.pk))

    @property
    def task_auth_token(self):
        '''Return temporary auth token used for task requests via API.'''
        if self.status == 'running':
            h = hmac.new(settings.SECRET_KEY, self.created.isoformat(), digestmod=hashlib.sha1)
            return '%d-%s' % (self.pk, h.hexdigest())

    @property
    def ask_diff_mode_on_launch(self):
        if self.job_template is not None:
            return self.job_template.ask_diff_mode_on_launch
        return False

    @property
    def ask_variables_on_launch(self):
        if self.job_template is not None:
            return self.job_template.ask_variables_on_launch
        return False

    @property
    def ask_limit_on_launch(self):
        if self.job_template is not None:
            return self.job_template.ask_limit_on_launch
        return False

    @property
    def ask_tags_on_launch(self):
        if self.job_template is not None:
            return self.job_template.ask_tags_on_launch
        return False

    @property
    def ask_skip_tags_on_launch(self):
        if self.job_template is not None:
            return self.job_template.ask_skip_tags_on_launch
        return False

    @property
    def ask_job_type_on_launch(self):
        if self.job_template is not None:
            return self.job_template.ask_job_type_on_launch
        return False

    @property
    def ask_verbosity_on_launch(self):
        if self.job_template is not None:
            return self.job_template.ask_verbosity_on_launch
        return False

    @property
    def ask_inventory_on_launch(self):
        if self.job_template is not None:
            return self.job_template.ask_inventory_on_launch
        return False

    @property
    def ask_credential_on_launch(self):
        if self.job_template is not None:
            return self.job_template.ask_credential_on_launch
        return False

    def get_passwords_needed_to_start(self):
        return self.passwords_needed_to_start

    def _get_hosts(self, **kwargs):
        from awx.main.models.inventory import Host
        kwargs['job_host_summaries__job__pk'] = self.pk
        return Host.objects.filter(**kwargs)

    @property
    def task_impact(self):
        # NOTE: We sorta have to assume the host count matches and that forks default to 5
        from awx.main.models.inventory import Host
        if self.launch_type == 'callback':
            count_hosts = 1
        else:
            count_hosts = Host.objects.filter(inventory__jobs__pk=self.pk).count()
        return min(count_hosts, 5 if self.forks == 0 else self.forks) * 10

    @property
    def successful_hosts(self):
        return self._get_hosts(job_host_summaries__ok__gt=0)

    @property
    def failed_hosts(self):
        return self._get_hosts(job_host_summaries__failures__gt=0)

    @property
    def changed_hosts(self):
        return self._get_hosts(job_host_summaries__changed__gt=0)

    @property
    def dark_hosts(self):
        return self._get_hosts(job_host_summaries__dark__gt=0)

    @property
    def unreachable_hosts(self):
        return self.dark_hosts

    @property
    def skipped_hosts(self):
        return self._get_hosts(job_host_summaries__skipped__gt=0)

    @property
    def processed_hosts(self):
        return self._get_hosts(job_host_summaries__processed__gt=0)

    def notification_data(self, block=5):
        data = super(Job, self).notification_data()
        all_hosts = {}
        # NOTE: Probably related to job event slowness, remove at some point -matburt
        if block:
            summaries = self.job_host_summaries.all()
            while block > 0 and not len(summaries):
                time.sleep(1)
                block -= 1
        else:
            summaries = self.job_host_summaries.all()
        for h in self.job_host_summaries.all():
            all_hosts[h.host_name] = dict(failed=h.failed,
                                          changed=h.changed,
                                          dark=h.dark,
                                          failures=h.failures,
                                          ok=h.ok,
                                          processed=h.processed,
                                          skipped=h.skipped)
        data.update(dict(inventory=self.inventory.name if self.inventory else None,
                         project=self.project.name if self.project else None,
                         playbook=self.playbook,
                         credential=self.credential.name if self.credential else None,
                         limit=self.limit,
                         extra_vars=self.display_extra_vars(),
                         hosts=all_hosts))
        return data

    def _resources_sufficient_for_launch(self):
        return not (self.inventory_id is None or self.project_id is None)

    def display_artifacts(self):
        '''
        Hides artifacts if they are marked as no_log type artifacts.
        '''
        artifacts = self.artifacts
        if artifacts.get('_ansible_no_log', False):
            return "$hidden due to Ansible no_log flag$"
        return artifacts

    @property
    def preferred_instance_groups(self):
        if self.project is not None and self.project.organization is not None:
            organization_groups = [x for x in self.project.organization.instance_groups.all()]
        else:
            organization_groups = []
        if self.inventory is not None:
            inventory_groups = [x for x in self.inventory.instance_groups.all()]
        else:
            inventory_groups = []
        if self.job_template is not None:
            template_groups = [x for x in self.job_template.instance_groups.all()]
        else:
            template_groups = []
        selected_groups = template_groups + inventory_groups + organization_groups
        if not selected_groups:
            return self.global_instance_groups
        return selected_groups

    # Job Credential required
    @property
    def can_start(self):
        if not super(Job, self).can_start:
            return False

        if not (self.credential) and not (self.vault_credential):
            return False

        return True

    '''
    JobNotificationMixin
    '''
    def get_notification_templates(self):
        if not self.job_template:
            return NotificationTemplate.objects.none()
        return self.job_template.notification_templates

    def get_notification_friendly_name(self):
        return "Job"

    @property
    def memcached_fact_key(self):
        return '{}'.format(self.inventory.id)

    def memcached_fact_host_key(self, host_name):
        return '{}-{}'.format(self.inventory.id, base64.b64encode(host_name.encode('utf-8')))

    def memcached_fact_modified_key(self, host_name):
        return '{}-{}-modified'.format(self.inventory.id, base64.b64encode(host_name.encode('utf-8')))

    def _get_inventory_hosts(self, only=['name', 'ansible_facts', 'modified',]):
        return self.inventory.hosts.only(*only)

    def _get_memcache_connection(self):
        return memcache.Client([settings.CACHES['default']['LOCATION']], debug=0)

    def start_job_fact_cache(self):
        if not self.inventory:
            return

        cache = self._get_memcache_connection()

        host_names = []

        for host in self._get_inventory_hosts():
            host_key = self.memcached_fact_host_key(host.name)
            modified_key = self.memcached_fact_modified_key(host.name)

            if cache.get(modified_key) is None:
                if host.ansible_facts_modified:
                    host_modified = host.ansible_facts_modified.replace(tzinfo=tzutc()).isoformat()
                else:
                    host_modified = datetime.datetime.now(tzutc()).isoformat()
                cache.set(host_key, json.dumps(host.ansible_facts))
                cache.set(modified_key, host_modified)

            host_names.append(host.name)

        cache.set(self.memcached_fact_key, host_names)

    def finish_job_fact_cache(self):
        if not self.inventory:
            return

        cache = self._get_memcache_connection()

        hosts = self._get_inventory_hosts()
        for host in hosts:
            host_key = self.memcached_fact_host_key(host.name)
            modified_key = self.memcached_fact_modified_key(host.name)

            modified = cache.get(modified_key)
            if modified is None:
                cache.delete(host_key)
                continue

            # Save facts if cache is newer than DB
            modified = parser.parse(modified, tzinfos=[tzutc()])
            if not host.ansible_facts_modified or modified > host.ansible_facts_modified:
                ansible_facts = cache.get(host_key)
                try:
                    ansible_facts = json.loads(ansible_facts)
                except Exception:
                    ansible_facts = None

                if ansible_facts is None:
                    cache.delete(host_key)
                    continue
                host.ansible_facts = ansible_facts
                host.ansible_facts_modified = modified
                if 'insights' in ansible_facts and 'system_id' in ansible_facts['insights']:
                    host.insights_system_id = ansible_facts['insights']['system_id']
                host.save()
                system_tracking_logger.info(
                    'New fact for inventory {} host {}'.format(
                        smart_str(host.inventory.name), smart_str(host.name)),
                    extra=dict(inventory_id=host.inventory.id, host_name=host.name,
                               ansible_facts=host.ansible_facts,
                               ansible_facts_modified=host.ansible_facts_modified.isoformat()))


class JobHostSummary(CreatedModifiedModel):
    '''
    Per-host statistics for each job.
    '''

    class Meta:
        app_label = 'main'
        unique_together = [('job', 'host_name')]
        verbose_name_plural = _('job host summaries')
        ordering = ('-pk',)

    job = models.ForeignKey(
        'Job',
        related_name='job_host_summaries',
        on_delete=models.CASCADE,
        editable=False,
    )
    host = models.ForeignKey('Host',
                             related_name='job_host_summaries',
                             null=True,
                             default=None,
                             on_delete=models.SET_NULL,
                             editable=False)

    host_name = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )

    changed = models.PositiveIntegerField(default=0, editable=False)
    dark = models.PositiveIntegerField(default=0, editable=False)
    failures = models.PositiveIntegerField(default=0, editable=False)
    ok = models.PositiveIntegerField(default=0, editable=False)
    processed = models.PositiveIntegerField(default=0, editable=False)
    skipped = models.PositiveIntegerField(default=0, editable=False)
    failed = models.BooleanField(default=False, editable=False)

    def __unicode__(self):
        hostname = self.host.name if self.host else 'N/A'
        return '%s changed=%d dark=%d failures=%d ok=%d processed=%d skipped=%s' % \
            (hostname, self.changed, self.dark, self.failures, self.ok,
             self.processed, self.skipped)

    def get_absolute_url(self, request=None):
        return reverse('api:job_host_summary_detail', kwargs={'pk': self.pk}, request=request)

    def save(self, *args, **kwargs):
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        if self.host is not None:
            self.host_name = self.host.name
        update_fields = kwargs.get('update_fields', [])
        self.failed = bool(self.dark or self.failures)
        update_fields.append('failed')
        super(JobHostSummary, self).save(*args, **kwargs)
        self.update_host_last_job_summary()

    def update_host_last_job_summary(self):
        update_fields = []
        if self.host is None:
            return
        if self.host.last_job_id != self.job_id:
            self.host.last_job_id = self.job_id
            update_fields.append('last_job_id')
        if self.host.last_job_host_summary_id != self.id:
            self.host.last_job_host_summary_id = self.id
            update_fields.append('last_job_host_summary_id')
        if update_fields:
            self.host.save(update_fields=update_fields)
        #self.host.update_computed_fields()


class JobEvent(CreatedModifiedModel):
    '''
    An event/message logged from the callback when running a job.
    '''

    # Playbook events will be structured to form the following hierarchy:
    # - playbook_on_start (once for each playbook file)
    #   - playbook_on_vars_prompt (for each play, but before play starts, we
    #     currently don't handle responding to these prompts)
    #   - playbook_on_play_start (once for each play)
    #     - playbook_on_import_for_host (not logged, not used for v2)
    #     - playbook_on_not_import_for_host (not logged, not used for v2)
    #     - playbook_on_no_hosts_matched
    #     - playbook_on_no_hosts_remaining
    #     - playbook_on_include (only v2 - only used for handlers?)
    #     - playbook_on_setup (not used for v2)
    #       - runner_on*
    #     - playbook_on_task_start (once for each task within a play)
    #       - runner_on_failed
    #       - runner_on_ok
    #       - runner_on_error (not used for v2)
    #       - runner_on_skipped
    #       - runner_on_unreachable
    #       - runner_on_no_hosts (not used for v2)
    #       - runner_on_async_poll (not used for v2)
    #       - runner_on_async_ok (not used for v2)
    #       - runner_on_async_failed (not used for v2)
    #       - runner_on_file_diff (v2 event is v2_on_file_diff)
    #       - runner_item_on_ok (v2 only)
    #       - runner_item_on_failed (v2 only)
    #       - runner_item_on_skipped (v2 only)
    #       - runner_retry (v2 only)
    #     - playbook_on_notify (once for each notification from the play, not used for v2)
    #   - playbook_on_stats

    EVENT_TYPES = [
        # (level, event, verbose name, failed)
        (3, 'runner_on_failed', _('Host Failed'), True),
        (3, 'runner_on_ok', _('Host OK'), False),
        (3, 'runner_on_error', _('Host Failure'), True),
        (3, 'runner_on_skipped', _('Host Skipped'), False),
        (3, 'runner_on_unreachable', _('Host Unreachable'), True),
        (3, 'runner_on_no_hosts', _('No Hosts Remaining'), False),
        (3, 'runner_on_async_poll', _('Host Polling'), False),
        (3, 'runner_on_async_ok', _('Host Async OK'), False),
        (3, 'runner_on_async_failed', _('Host Async Failure'), True),
        (3, 'runner_item_on_ok', _('Item OK'), False),
        (3, 'runner_item_on_failed', _('Item Failed'), True),
        (3, 'runner_item_on_skipped', _('Item Skipped'), False),
        (3, 'runner_retry', _('Host Retry'), False),
        # Tower does not yet support --diff mode.
        (3, 'runner_on_file_diff', _('File Difference'), False),
        (0, 'playbook_on_start', _('Playbook Started'), False),
        (2, 'playbook_on_notify', _('Running Handlers'), False),
        (2, 'playbook_on_include', _('Including File'), False),
        (2, 'playbook_on_no_hosts_matched', _('No Hosts Matched'), False),
        (2, 'playbook_on_no_hosts_remaining', _('No Hosts Remaining'), False),
        (2, 'playbook_on_task_start', _('Task Started'), False),
        # Tower does not yet support vars_prompt (and will probably hang :)
        (1, 'playbook_on_vars_prompt', _('Variables Prompted'), False),
        (2, 'playbook_on_setup', _('Gathering Facts'), False),
        (2, 'playbook_on_import_for_host', _('internal: on Import for Host'), False),
        (2, 'playbook_on_not_import_for_host', _('internal: on Not Import for Host'), False),
        (1, 'playbook_on_play_start', _('Play Started'), False),
        (1, 'playbook_on_stats', _('Playbook Complete'), False),

        # Additional event types for captured stdout not directly related to
        # playbook or runner events.
        (0, 'debug', _('Debug'), False),
        (0, 'verbose', _('Verbose'), False),
        (0, 'deprecated', _('Deprecated'), False),
        (0, 'warning', _('Warning'), False),
        (0, 'system_warning', _('System Warning'), False),
        (0, 'error', _('Error'), True),
    ]
    FAILED_EVENTS = [x[1] for x in EVENT_TYPES if x[3]]
    EVENT_CHOICES = [(x[1], x[2]) for x in EVENT_TYPES]
    LEVEL_FOR_EVENT = dict([(x[1], x[0]) for x in EVENT_TYPES])

    class Meta:
        app_label = 'main'
        ordering = ('pk',)
        index_together = [
            ('job', 'event'),
            ('job', 'uuid'),
            ('job', 'start_line'),
            ('job', 'end_line'),
            ('job', 'parent_uuid'),
        ]

    job = models.ForeignKey(
        'Job',
        related_name='job_events',
        on_delete=models.CASCADE,
        editable=False,
    )
    event = models.CharField(
        max_length=100,
        choices=EVENT_CHOICES,
    )
    event_data = JSONField(
        blank=True,
        default={},
    )
    failed = models.BooleanField(
        default=False,
        editable=False,
    )
    changed = models.BooleanField(
        default=False,
        editable=False,
    )
    uuid = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    host = models.ForeignKey(
        'Host',
        related_name='job_events_as_primary_host',
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        editable=False,
    )
    host_name = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    hosts = models.ManyToManyField(
        'Host',
        related_name='job_events',
        editable=False,
    )
    playbook = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    play = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    role = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    task = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    parent = models.ForeignKey(
        'self',
        related_name='children',
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        editable=False,
    )
    parent_uuid = models.CharField(
        max_length=1024,
        default='',
        editable=False,
    )
    counter = models.PositiveIntegerField(
        default=0,
        editable=False,
    )
    stdout = models.TextField(
        default='',
        editable=False,
    )
    verbosity = models.PositiveIntegerField(
        default=0,
        editable=False,
    )
    start_line = models.PositiveIntegerField(
        default=0,
        editable=False,
    )
    end_line = models.PositiveIntegerField(
        default=0,
        editable=False,
    )

    def get_absolute_url(self, request=None):
        return reverse('api:job_event_detail', kwargs={'pk': self.pk}, request=request)

    def __unicode__(self):
        return u'%s @ %s' % (self.get_event_display2(), self.created.isoformat())

    @property
    def event_level(self):
        return self.LEVEL_FOR_EVENT.get(self.event, 0)

    def get_event_display2(self):
        msg = self.get_event_display()
        if self.event == 'playbook_on_play_start':
            if self.play:
                msg = "%s (%s)" % (msg, self.play)
        elif self.event == 'playbook_on_task_start':
            if self.task:
                if self.event_data.get('is_conditional', False):
                    msg = 'Handler Notified'
                if self.role:
                    msg = '%s (%s | %s)' % (msg, self.role, self.task)
                else:
                    msg = "%s (%s)" % (msg, self.task)

        # Change display for runner events trigged by async polling.  Some of
        # these events may not show in most cases, due to filterting them out
        # of the job event queryset returned to the user.
        res = self.event_data.get('res', {})
        # Fix for existing records before we had added the workaround on save
        # to change async_ok to async_failed.
        if self.event == 'runner_on_async_ok':
            try:
                if res.get('failed', False) or res.get('rc', 0) != 0:
                    msg = 'Host Async Failed'
            except (AttributeError, TypeError):
                pass
        # Runner events with ansible_job_id are part of async starting/polling.
        if self.event in ('runner_on_ok', 'runner_on_failed'):
            try:
                module_name = res['invocation']['module_name']
                job_id = res['ansible_job_id']
            except (TypeError, KeyError, AttributeError):
                module_name = None
                job_id = None
            if module_name and job_id:
                if module_name == 'async_status':
                    msg = 'Host Async Checking'
                else:
                    msg = 'Host Async Started'
        # Handle both 1.2 on_failed and 1.3+ on_async_failed events when an
        # async task times out.
        if self.event in ('runner_on_failed', 'runner_on_async_failed'):
            try:
                if res['msg'] == 'timed out':
                    msg = 'Host Async Timeout'
            except (TypeError, KeyError, AttributeError):
                pass
        return msg

    def _update_from_event_data(self):
        # Update job event model fields from event data.
        updated_fields = set()
        job = self.job
        verbosity = job.verbosity
        event_data = self.event_data
        res = event_data.get('res', None)
        if self.event in self.FAILED_EVENTS and not event_data.get('ignore_errors', False):
            self.failed = True
            updated_fields.add('failed')
        if isinstance(res, dict):
            if res.get('changed', False):
                self.changed = True
                updated_fields.add('changed')
            # If we're not in verbose mode, wipe out any module arguments.
            invocation = res.get('invocation', None)
            if isinstance(invocation, dict) and verbosity == 0 and 'module_args' in invocation:
                event_data['res']['invocation']['module_args'] = ''
                self.event_data = event_data
                updated_fields.add('event_data')
        if self.event == 'playbook_on_stats':
            try:
                failures_dict = event_data.get('failures', {})
                dark_dict = event_data.get('dark', {})
                self.failed = bool(sum(failures_dict.values()) +
                                   sum(dark_dict.values()))
                updated_fields.add('failed')
                changed_dict = event_data.get('changed', {})
                self.changed = bool(sum(changed_dict.values()))
                updated_fields.add('changed')
            except (AttributeError, TypeError):
                pass
        for field in ('playbook', 'play', 'task', 'role', 'host'):
            value = force_text(event_data.get(field, '')).strip()
            if field == 'host':
                field = 'host_name'
            if value != getattr(self, field):
                setattr(self, field, value)
                updated_fields.add(field)
        return updated_fields

    def _update_parents_failed_and_changed(self):
        # Update parent events to reflect failed, changed
        runner_events = JobEvent.objects.filter(job=self.job,
                                                event__startswith='runner_on')
        changed_events = runner_events.filter(changed=True)
        failed_events = runner_events.filter(failed=True)
        JobEvent.objects.filter(uuid__in=changed_events.values_list('parent_uuid', flat=True)).update(changed=True)
        JobEvent.objects.filter(uuid__in=failed_events.values_list('parent_uuid', flat=True)).update(failed=True)

    def _update_hosts(self, extra_host_pks=None):
        # Update job event hosts m2m from host_name, propagate to parent events.
        extra_host_pks = set(extra_host_pks or [])
        hostnames = set()
        if self.host_name:
            hostnames.add(self.host_name)
        if self.event == 'playbook_on_stats':
            try:
                for v in self.event_data.values():
                    hostnames.update(v.keys())
            except AttributeError: # In case event_data or v isn't a dict.
                pass
        qs = self.job.inventory.hosts.all()
        qs = qs.filter(Q(name__in=hostnames) | Q(pk__in=extra_host_pks))
        qs = qs.exclude(job_events__pk=self.id).only('id')
        for host in qs:
            self.hosts.add(host)
        if self.parent_uuid:
            parent = JobEvent.objects.filter(uuid=self.parent_uuid)
            if parent.exists():
                parent = parent[0]
                parent._update_hosts(qs.values_list('id', flat=True))

    def _hostnames(self):
        hostnames = set()
        try:
            for stat in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
                hostnames.update(self.event_data.get(stat, {}).keys())
        except AttributeError:  # In case event_data or v isn't a dict.
            pass
        return hostnames

    def _update_host_summary_from_stats(self, hostnames):
        with ignore_inventory_computed_fields():
            qs = self.job.inventory.hosts.filter(name__in=hostnames)
            job = self.job
            for host in hostnames:
                host_stats = {}
                for stat in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
                    try:
                        host_stats[stat] = self.event_data.get(stat, {}).get(host, 0)
                    except AttributeError:  # in case event_data[stat] isn't a dict.
                        pass
                if qs.filter(name=host).exists():
                    host_actual = qs.get(name=host)
                    host_summary, created = job.job_host_summaries.get_or_create(host=host_actual, host_name=host_actual.name, defaults=host_stats)
                else:
                    host_summary, created = job.job_host_summaries.get_or_create(host_name=host, defaults=host_stats)

                if not created:
                    update_fields = []
                    for stat, value in host_stats.items():
                        if getattr(host_summary, stat) != value:
                            setattr(host_summary, stat, value)
                            update_fields.append(stat)
                    if update_fields:
                        host_summary.save(update_fields=update_fields)

    def save(self, *args, **kwargs):
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # Update model fields and related objects unless we're only updating
        # failed/changed flags triggered from a child event.
        from_parent_update = kwargs.pop('from_parent_update', False)
        if not from_parent_update:
            # Update model fields from event data.
            updated_fields = self._update_from_event_data()
            for field in updated_fields:
                if field not in update_fields:
                    update_fields.append(field)
            # Update host related field from host_name.
            if not self.host_id and self.host_name:
                host_qs = self.job.inventory.hosts.filter(name=self.host_name)
                host_id = host_qs.only('id').values_list('id', flat=True).first()
                if host_id != self.host_id:
                    self.host_id = host_id
                    if 'host_id' not in update_fields:
                        update_fields.append('host_id')
        super(JobEvent, self).save(*args, **kwargs)
        # Update related objects after this event is saved.
        if not from_parent_update:
            if getattr(settings, 'CAPTURE_JOB_EVENT_HOSTS', False):
                self._update_hosts()
            if self.event == 'playbook_on_stats':
                self._update_parents_failed_and_changed()

                hostnames = self._hostnames()
                self._update_host_summary_from_stats(hostnames)
                self.job.inventory.update_computed_fields()

                emit_channel_notification('jobs-summary', dict(group_name='jobs', unified_job_id=self.job.id))

    @classmethod
    def create_from_data(self, **kwargs):
        # Must have a job_id specified.
        if not kwargs.get('job_id', None):
            return

        # Convert the datetime for the job event's creation appropriately,
        # and include a time zone for it.
        #
        # In the event of any issue, throw it out, and Django will just save
        # the current time.
        try:
            if not isinstance(kwargs['created'], datetime.datetime):
                kwargs['created'] = parse_datetime(kwargs['created'])
            if not kwargs['created'].tzinfo:
                kwargs['created'] = kwargs['created'].replace(tzinfo=utc)
        except (KeyError, ValueError):
            kwargs.pop('created', None)

        # Sanity check: Don't honor keys that we don't recognize.
        valid_keys = {'job_id', 'event', 'event_data', 'playbook', 'play',
                      'role', 'task', 'created', 'counter', 'uuid', 'stdout',
                      'parent_uuid', 'start_line', 'end_line', 'verbosity'}
        for key in kwargs.keys():
            if key not in valid_keys:
                kwargs.pop(key)

        event_data = kwargs.get('event_data', None)
        artifact_dict = None
        if event_data:
            artifact_dict = event_data.pop('artifact_data', None)

        job_event = JobEvent.objects.create(**kwargs)

        analytics_logger.info('Job event data saved.', extra=dict(python_objects=dict(job_event=job_event)))

        # Save artifact data to parent job (if provided).
        if artifact_dict:
            if event_data and isinstance(event_data, dict):
                # Note: Core has not added support for marking artifacts as
                # sensitive yet. Going forward, core will not use
                # _ansible_no_log to denote sensitive set_stats calls.
                # Instead, they plan to add a flag outside of the traditional
                # no_log mechanism. no_log will not work for this feature,
                # in core, because sensitive data is scrubbed before sending
                # data to the callback. The playbook_on_stats is the callback
                # in which the set_stats data is used.

                # Again, the sensitive artifact feature has not yet landed in
                # core. The below is how we mark artifacts payload as
                # senstive
                # artifact_dict['_ansible_no_log'] = True
                #
                parent_job = Job.objects.filter(pk=kwargs['job_id']).first()
                if parent_job and parent_job.artifacts != artifact_dict:
                    parent_job.artifacts = artifact_dict
                    parent_job.save(update_fields=['artifacts'])

        return job_event

    @classmethod
    def get_startevent_queryset(cls, parent_task, starting_events, ordering=None):
        '''
        We need to pull information about each start event.

        This is super tricky, because this table has a one-to-many
        relationship with itself (parent-child), and we're getting
        information for an arbitrary number of children. This means we
        need stats on grandchildren, sorted by child.
        '''
        qs = (JobEvent.objects.filter(parent__parent=parent_task,
                                      parent__event__in=starting_events)
                              .values('parent__id', 'event', 'changed')
                              .annotate(num=Count('event'))
                              .order_by('parent__id'))
        if ordering is not None:
            qs = qs.order_by(ordering)
        return qs


class SystemJobOptions(BaseModel):
    '''
    Common fields for SystemJobTemplate and SystemJob.
    '''

    SYSTEM_JOB_TYPE = [
        ('cleanup_jobs', _('Remove jobs older than a certain number of days')),
        ('cleanup_activitystream', _('Remove activity stream entries older than a certain number of days')),
        ('cleanup_facts', _('Purge and/or reduce the granularity of system tracking data')),
    ]

    class Meta:
        abstract = True

    job_type = models.CharField(
        max_length=32,
        choices=SYSTEM_JOB_TYPE,
        blank=True,
        default='',
    )


class SystemJobTemplate(UnifiedJobTemplate, SystemJobOptions):

    class Meta:
        app_label = 'main'

    @classmethod
    def _get_unified_job_class(cls):
        return SystemJob

    @classmethod
    def _get_unified_job_field_names(cls):
        return ['name', 'description', 'job_type', 'extra_vars']

    def get_absolute_url(self, request=None):
        return reverse('api:system_job_template_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def cache_timeout_blocked(self):
        return False

    @property
    def notification_templates(self):
        # TODO: Go through RBAC instead of calling all(). Need to account for orphaned NotificationTemplates
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


class SystemJob(UnifiedJob, SystemJobOptions, JobNotificationMixin):

    class Meta:
        app_label = 'main'
        ordering = ('id',)

    system_job_template = models.ForeignKey(
        'SystemJobTemplate',
        related_name='jobs',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    extra_vars = prevent_search(models.TextField(
        blank=True,
        default='',
    ))

    extra_vars_dict = VarsDictProperty('extra_vars', True)

    @classmethod
    def _get_parent_field_name(cls):
        return 'system_job_template'

    @classmethod
    def _get_task_class(cls):
        from awx.main.tasks import RunSystemJob
        return RunSystemJob

    def websocket_emit_data(self):
        return {}

    def get_absolute_url(self, request=None):
        return reverse('api:system_job_detail', kwargs={'pk': self.pk}, request=request)

    def get_ui_url(self):
        return urljoin(settings.TOWER_URL_BASE, "/#/management_jobs/{}".format(self.pk))

    @property
    def task_impact(self):
        return 150

    @property
    def preferred_instance_groups(self):
        return self.global_instance_groups

    '''
    JobNotificationMixin
    '''
    def get_notification_templates(self):
        return self.system_job_template.notification_templates

    def get_notification_friendly_name(self):
        return "System Job"

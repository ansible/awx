# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import hmac
import json
import logging
import os
import shlex

# PyYAML
import yaml

# Django
from django.conf import settings
from django.db import models
from django.db.models import CASCADE, SET_NULL, PROTECT
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now

# Django-JSONField
from jsonfield import JSONField

# Django-Taggit
from taggit.managers import TaggableManager

# Django-Celery
from djcelery.models import TaskMeta

__all__ = ['PrimordialModel', 'Organization', 'Team', 'Project', 'Credential',
           'Inventory', 'Host', 'Group', 'Permission', 'JobTemplate', 'Job',
           'JobHostSummary', 'JobEvent', 'PERM_INVENTORY_ADMIN',
           'PERM_INVENTORY_READ', 'PERM_INVENTORY_WRITE',
           'PERM_INVENTORY_DEPLOY', 'PERM_INVENTORY_CHECK']

logger = logging.getLogger('awx.main.models')

# TODO: reporting model TBD

PERM_INVENTORY_ADMIN  = 'admin'
PERM_INVENTORY_READ   = 'read'
PERM_INVENTORY_WRITE  = 'write'
PERM_INVENTORY_DEPLOY = 'run'
PERM_INVENTORY_CHECK  = 'check'

JOB_TYPE_CHOICES = [
    (PERM_INVENTORY_DEPLOY, _('Run')),
    (PERM_INVENTORY_CHECK, _('Check')),
]

# FIXME: TODO: make sure all of these are used and consistent
PERMISSION_TYPE_CHOICES = [
    (PERM_INVENTORY_READ, _('Read Inventory')),
    (PERM_INVENTORY_WRITE, _('Edit Inventory')),
    (PERM_INVENTORY_ADMIN, _('Administrate Inventory')),
    (PERM_INVENTORY_DEPLOY, _('Deploy To Inventory')),
    (PERM_INVENTORY_CHECK, _('Deploy To Inventory (Dry Run)')),
]

class PrimordialModel(models.Model):
    '''
    common model for all object types that have these standard fields
    must use a subclass CommonModel or CommonModelNameNotUnique though
    as this lacks a name field.
    '''

    class Meta:
        abstract = True

    description   = models.TextField(blank=True, default='')
    created_by    = models.ForeignKey('auth.User', 
                        on_delete=SET_NULL, null=True, 
                        related_name='%s(class)s_created', 
                        editable=False) # not blank=False on purpose for admin!
    created       = models.DateTimeField(auto_now_add=True)
    active        = models.BooleanField(default=True)

    tags = TaggableManager(blank=True)

    def __unicode__(self):
        return unicode("%s-%s"% (self.name, self.id))

    def save(self, *args, **kwargs):
        # For compatibility with Django 1.4.x, attempt to handle any calls to
        # save that pass update_fields.
        try:
            super(PrimordialModel, self).save(*args, **kwargs)
        except TypeError:
            if 'update_fields' not in kwargs:
                raise
            kwargs.pop('update_fields')
            super(PrimordialModel, self).save(*args, **kwargs)

    def mark_inactive(self, save=True):
        '''Use instead of delete to rename and mark inactive.'''

        if self.active:
            if 'name' in self._meta.get_all_field_names():
                self.name   = "_deleted_%s_%s" % (now().isoformat(), self.name)
            self.active = False
            if save:
                self.save()

class CommonModel(PrimordialModel):
    ''' a base model where the name is unique '''

    class Meta:
        abstract = True

    name          = models.CharField(max_length=512, unique=True)

class CommonModelNameNotUnique(PrimordialModel):
    ''' a base model where the name is not unique '''

    class Meta:
        abstract = True

    name          = models.CharField(max_length=512, unique=False)

class Organization(CommonModel):
    '''
    organizations are the basic unit of multi-tenancy divisions
    '''

    class Meta:
        app_label = 'main'

    users    = models.ManyToManyField('auth.User', blank=True, related_name='organizations')
    admins   = models.ManyToManyField('auth.User', blank=True, related_name='admin_of_organizations')
    projects = models.ManyToManyField('Project', blank=True, related_name='organizations')

    def get_absolute_url(self):
        return reverse('main:organization_detail', args=(self.pk,))

    def __unicode__(self):
        return self.name

class Inventory(CommonModel):
    '''
    an inventory source contains lists and hosts.
    '''

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('inventories')
        unique_together = (("name", "organization"),)

    organization = models.ForeignKey(Organization, null=False, related_name='inventories')
    variables = models.TextField(
        blank=True,
        default='',
        null=True,
        help_text=_('Variables in JSON or YAML format.'),
    )
    has_active_failures = models.BooleanField(default=False, editable=False)

    def get_absolute_url(self):
        return reverse('main:inventory_detail', args=(self.pk,))

    @property
    def variables_dict(self):
        try:
            return json.loads(self.variables.strip() or '{}')
        except ValueError:
            return yaml.safe_load(self.variables)

    def update_has_active_failures(self, update_groups=True, update_hosts=True):
        if update_hosts:
            for host in self.hosts.filter(active=True):
                host.update_has_active_failures(update_inventory=False,
                                                update_groups=False)
        if update_groups:
            for group in self.groups.filter(active=True):
                group.update_has_active_failures()
        failed_hosts = self.hosts.filter(active=True, has_active_failures=True)
        has_active_failures = bool(failed_hosts.count())
        if self.has_active_failures != has_active_failures:
            self.has_active_failures = has_active_failures
            self.save()

class Host(CommonModelNameNotUnique):
    '''
    A managed node
    '''

    class Meta:
        app_label = 'main'
        unique_together = (("name", "inventory"),)

    variables = models.TextField(
        blank=True,
        default='',
        help_text=_('Variables in JSON or YAML format.'),
    )

    inventory               = models.ForeignKey('Inventory', null=False, related_name='hosts')
    last_job                = models.ForeignKey('Job', blank=True, null=True, default=None, on_delete=models.SET_NULL, related_name='hosts_as_last_job+')
    last_job_host_summary   = models.ForeignKey('JobHostSummary', blank=True, null=True, default=None, on_delete=models.SET_NULL, related_name='hosts_as_last_job_summary+')
    has_active_failures     = models.BooleanField(default=False, editable=False)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:host_detail', args=(self.pk,))

    def update_has_active_failures(self, update_inventory=True,
                                   update_groups=True):
        has_active_failures = bool(self.last_job_host_summary and
                                   self.last_job_host_summary.job.active and
                                   self.last_job_host_summary.failed)
        if self.has_active_failures != has_active_failures:
            self.has_active_failures = has_active_failures
            self.save()
        if update_inventory:
            self.inventory.update_has_active_failures(update_groups=False,
                                                      update_hosts=False)
        if update_groups:
            for group in self.all_groups.filter(active=True):
                group.update_has_active_failures()

    @property
    def variables_dict(self):
        try:
            return json.loads(self.variables.strip() or '{}')
        except ValueError:
            return yaml.safe_load(self.variables)

    @property
    def all_groups(self):
        '''
        Return all groups of which this host is a member, avoiding infinite
        recursion in the case of cyclical group relations.
        '''
        qs = self.groups.distinct()
        for group in self.groups.all():
            qs = qs | group.all_parents
        return qs

    # Use .job_host_summaries.all() to get jobs affecting this host.
    # Use .job_events.all() to get events affecting this host.

class Group(CommonModelNameNotUnique):
    '''
    A group containing managed hosts.  A group or host may belong to multiple
    groups.
    '''

    class Meta:
        app_label = 'main'
        unique_together = (("name", "inventory"),)

    inventory     = models.ForeignKey('Inventory', null=False, related_name='groups')
    # Can also be thought of as: parents == member_of, children == members
    parents       = models.ManyToManyField('self', symmetrical=False, related_name='children', blank=True)
    variables = models.TextField(
        blank=True,
        default='',
        help_text=_('Variables in JSON or YAML format.'),
    )
    hosts         = models.ManyToManyField('Host', related_name='groups', blank=True)
    has_active_failures = models.BooleanField(default=False, editable=False)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:group_detail', args=(self.pk,))

    def update_has_active_failures(self):
        failed_hosts = self.all_hosts.filter(active=True,
                                             last_job_host_summary__job__active=True,
                                             last_job_host_summary__failed=True)
        has_active_failures = bool(failed_hosts.count())
        if self.has_active_failures != has_active_failures:
            self.has_active_failures = has_active_failures
            self.save()

    @property
    def variables_dict(self):
        try:
            return json.loads(self.variables.strip() or '{}')
        except ValueError:
            return yaml.safe_load(self.variables)

    def get_all_parents(self, except_pks=None):
        '''
        Return all parents of this group recursively, avoiding infinite
        recursion in the case of cyclical relations.  The group itself will be
        excluded unless there is a cycle leading back to it.
        '''
        except_pks = except_pks or set()
        except_pks.add(self.pk)
        qs = self.parents.distinct()
        for group in self.parents.exclude(pk__in=except_pks):
            qs = qs | group.get_all_parents(except_pks)
        return qs

    @property
    def all_parents(self):
        return self.get_all_parents()

    def get_all_children(self, except_pks=None):
        '''
        Return all children of this group recursively, avoiding infinite
        recursion in the case of cyclical relations.  The group itself will be
        excluded unless there is a cycle leading back to it.
        '''
        except_pks = except_pks or set()
        except_pks.add(self.pk)
        qs = self.children.distinct()
        for group in self.children.exclude(pk__in=except_pks):
            qs = qs | group.get_all_children(except_pks)
        return qs

    @property
    def all_children(self):
        return self.get_all_children()

    def get_all_hosts(self, except_group_pks=None):
        '''
        Return all hosts associated with this group or any of its children,
        avoiding infinite recursion in the case of cyclical group relations.
        '''
        except_group_pks = except_group_pks or set()
        except_group_pks.add(self.pk)
        qs = self.hosts.distinct()
        for group in self.children.exclude(pk__in=except_group_pks):
            qs = qs | group.get_all_hosts(except_group_pks)
        return qs

    @property
    def all_hosts(self):
        return self.get_all_hosts()

    @property
    def job_host_summaries(self):
        return JobHostSummary.objects.filter(host__in=self.all_hosts)

    @property
    def job_events(self):
        return JobEvent.objects.filter(host__in=self.all_hosts)

class Credential(CommonModelNameNotUnique):
    '''
    A credential contains information about how to talk to a remote set of hosts
    Usually this is a SSH key location, and possibly an unlock password.
    If used with sudo, a sudo password should be set if required.
    '''

    class Meta:
        app_label = 'main'

    user            = models.ForeignKey('auth.User', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='credentials')
    team            = models.ForeignKey('Team', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='credentials')

    ssh_username = models.CharField(
        blank=True,
        default='',
        max_length=1024,
        verbose_name=_('SSH username'),
        help_text=_('SSH username for a job using this credential.'),
    )
    ssh_password = models.CharField(
        blank=True,
        default='',
        max_length=1024,
        verbose_name=_('SSH password'),
        help_text=_('SSH password (or "ASK" to prompt the user).'),
    )
    ssh_key_data = models.TextField(
        blank=True,
        default='',
        verbose_name=_('SSH private key'),
        help_text=_('RSA or DSA private key to be used instead of password.'),
    )
    ssh_key_unlock = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        verbose_name=_('SSH key unlock'),
        help_text=_('Passphrase to unlock SSH private key if encrypted (or '
                    '"ASK" to prompt the user).'),
    )
    sudo_username = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Sudo username for a job using this credential.'),
    )
    sudo_password = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Sudo password (or "ASK" to prompt the user).'),
    )

    @property
    def needs_ssh_password(self):
        return not self.ssh_key_data and self.ssh_password == 'ASK'

    @property
    def needs_ssh_key_unlock(self):
        return 'ENCRYPTED' in self.ssh_key_data and \
            (not self.ssh_key_unlock or self.ssh_key_unlock == 'ASK')

    @property
    def needs_sudo_password(self):
        return self.sudo_password == 'ASK'
    
    @property
    def passwords_needed(self):
        needed = []
        for field in ('ssh_password', 'sudo_password', 'ssh_key_unlock'):
            if getattr(self, 'needs_%s' % field):
                needed.append(field)
        return needed

    def get_absolute_url(self):
        return reverse('main:credential_detail', args=(self.pk,))

class Team(CommonModel):
    '''
    A team is a group of users that work on common projects.
    '''

    class Meta:
        app_label = 'main'

    projects        = models.ManyToManyField('Project', blank=True, related_name='teams')
    users           = models.ManyToManyField('auth.User', blank=True, related_name='teams')
    organization    = models.ForeignKey('Organization', blank=False, null=True, on_delete=SET_NULL, related_name='teams')

    def get_absolute_url(self):
        return reverse('main:team_detail', args=(self.pk,))

class Project(CommonModel):
    '''
    A project represents a playbook git repo that can access a set of inventories
    '''

    # this is not part of the project, but managed with perms
    # inventories      = models.ManyToManyField('Inventory', blank=True, related_name='projects')

    # Project files must be available on the server in folders directly
    # beneath the path specified by settings.PROJECTS_ROOT.  There is no way
    # via the API to upload/update a project or its playbooks; this must be
    # done by other means for now.

    @classmethod
    def get_local_path_choices(cls):
        if os.path.exists(settings.PROJECTS_ROOT):
            paths = [x for x in os.listdir(settings.PROJECTS_ROOT)
                     if os.path.isdir(os.path.join(settings.PROJECTS_ROOT, x))
                     and not x.startswith('.')]
            qs = Project.objects.filter(active=True)
            used_paths = qs.values_list('local_path', flat=True)
            return [x for x in paths if x not in used_paths]
        else:
            return []

    local_path = models.CharField(
        max_length=1024,
        # Not unique for now, otherwise "deletes" won't allow reusing the
        # same path for another active project.
        #unique=True,
        help_text=_('Local path (relative to PROJECTS_ROOT) containing '
                    'playbooks and related files for this project.')
    )
    #scm_type         = models.CharField(max_length=64)
    #default_playbook = models.CharField(max_length=1024)

    def get_absolute_url(self):
        return reverse('main:project_detail', args=(self.pk,))

    def get_project_path(self):
        local_path = os.path.basename(self.local_path)
        if local_path and not local_path.startswith('.'):
            proj_path = os.path.join(settings.PROJECTS_ROOT, local_path)
            if os.path.exists(proj_path):
                return proj_path

    @property
    def playbooks(self):
        results = []
        project_path = self.get_project_path()
        if project_path:
            for dirpath, dirnames, filenames in os.walk(project_path):
                for filename in filenames:
                    if os.path.splitext(filename)[-1] != '.yml':
                        continue
                    playbook = os.path.join(dirpath, filename)
                    # Filter any invalid YAML files.
                    try:
                        data = yaml.safe_load(file(playbook).read())
                    except (IOError, yaml.YAMLError):
                        continue
                    # Filter files that do not have either hosts or top-level
                    # includes.
                    try:
                        if 'hosts' not in data[0] and 'include' not in data[0]:
                            continue
                    except (TypeError, IndexError, KeyError):
                        continue
                    playbook = os.path.relpath(playbook, project_path)
                    # Filter files in a roles subdirectory.
                    if 'roles' in playbook.split(os.sep):
                        continue
                    # Filter files in a tasks subdirectory.
                    if 'tasks' in playbook.split(os.sep):
                        continue
                    results.append(playbook)
        return results

class Permission(CommonModelNameNotUnique):
    '''
    A permission allows a user, project, or team to be able to use an inventory source.
    '''

    class Meta:
        app_label = 'main'

    # permissions are granted to either a user or a team:
    user            = models.ForeignKey('auth.User', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')
    team            = models.ForeignKey('Team', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')

    # to be used against a project or inventory (or a project and inventory in conjunction):
    project         = models.ForeignKey('Project', null=True, on_delete=SET_NULL, blank=True, related_name='permissions')
    inventory       = models.ForeignKey('Inventory', null=True, on_delete=SET_NULL, related_name='permissions')

    # permission system explanation:
    #
    # for example, user A on inventory X has write permissions                 (PERM_INVENTORY_WRITE)
    #              team C on inventory X has read permissions                  (PERM_INVENTORY_READ)
    #              team C on inventory X and project Y has launch permissions  (PERM_INVENTORY_DEPLOY)
    #              team C on inventory X and project Z has dry run permissions (PERM_INVENTORY_CHECK)
    #
    # basically for launching, permissions can be awarded to the whole inventory source or just the inventory source
    # in context of a given project.
    #
    # the project parameter is not used when dealing with READ, WRITE, or ADMIN permissions.

    permission_type = models.CharField(max_length=64, choices=PERMISSION_TYPE_CHOICES)

    def __unicode__(self):
        return unicode("Permission(name=%s,ON(user=%s,team=%s),FOR(project=%s,inventory=%s,type=%s))" % (
            self.name,
            self.user,
            self.team,
            self.project,
            self.inventory,
            self.permission_type
        ))

    def get_absolute_url(self):
        return reverse('main:permission_detail', args=(self.pk,))

# TODO: other job types (later)

class JobTemplate(CommonModel):
    '''
    A job template is a reusable job definition for applying a project (with
    playbook) to an inventory source with a given credential.
    '''

    class Meta:
        app_label = 'main'

    job_type = models.CharField(
        max_length=64,
        choices=JOB_TYPE_CHOICES,
    )
    inventory = models.ForeignKey(
        'Inventory',
        related_name='job_templates',
        null=True,
        on_delete=models.SET_NULL,
    )
    project = models.ForeignKey(
        'Project',
        related_name='job_templates',
        null=True,
        on_delete=models.SET_NULL,
    )
    playbook = models.CharField(
        max_length=1024,
        default='',
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='job_templates',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
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
        blank=True,
        default=0,
    )
    extra_vars = models.TextField(
        blank=True,
        default='',
    )
    job_tags = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    host_config_key = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )

    def create_job(self, **kwargs):
        '''
        Create a new job based on this template.
        '''
        save_job = kwargs.pop('save', True)
        kwargs['job_template'] = self
        # Create new name with timestamp format to match jobs launched by the UI.
        new_name = '%s %s' % (self.name, now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
        new_name = new_name[:-4] + 'Z'
        kwargs.setdefault('name', new_name)
        kwargs.setdefault('description', self.description)
        kwargs.setdefault('job_type', self.job_type)
        kwargs.setdefault('inventory', self.inventory)
        kwargs.setdefault('project', self.project)
        kwargs.setdefault('playbook', self.playbook)
        kwargs.setdefault('credential', self.credential)
        kwargs.setdefault('forks', self.forks)
        kwargs.setdefault('limit', self.limit)
        kwargs.setdefault('verbosity', self.verbosity)
        kwargs.setdefault('extra_vars', self.extra_vars)
        kwargs.setdefault('job_tags', self.job_tags)
        job = Job(**kwargs)
        if save_job:
            job.save()
        return job

    def get_absolute_url(self):
        return reverse('main:job_template_detail', args=(self.pk,))

    def can_start_without_user_input(self):
        '''
        Return whether job template can be used to start a new job without
        requiring any user input.
        '''
        return bool(self.credential and not self.credential.passwords_needed)

class Job(CommonModelNameNotUnique):
    '''
    A job applies a project (with playbook) to an inventory source with a given
    credential.  It represents a single invocation of ansible-playbook with the
    given parameters.
    '''

    LAUNCH_TYPE_CHOICES = [
        ('manual', _('Manual')),
        ('callback', _('Callback')),
        ('scheduled', _('Scheduled')),
    ]

    STATUS_CHOICES = [
        ('new', _('New')),                  # Job has been created, but not started.
        ('pending', _('Pending')),          # Job has been queued, but is not yet running.
        ('running', _('Running')),          # Job is currently running.
        ('successful', _('Successful')),    # Job completed successfully.
        ('failed', _('Failed')),            # Job completed, but with failures.
        ('error', _('Error')),              # The job was unable to run.
        ('canceled', _('Canceled')),        # The job was canceled before completion.
    ]

    class Meta:
        app_label = 'main'

    job_template = models.ForeignKey(
        'JobTemplate',
        related_name='jobs',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    job_type = models.CharField(
        max_length=64,
        choices=JOB_TYPE_CHOICES,
    )
    inventory = models.ForeignKey(
        'Inventory',
        related_name='jobs',
        null=True,
        on_delete=models.SET_NULL,
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='jobs',
        null=True,
        on_delete=models.SET_NULL,
    )
    project = models.ForeignKey(
        'Project',
        related_name='jobs',
        null=True,
        on_delete=models.SET_NULL,
    )
    playbook = models.CharField(
        max_length=1024,
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
        blank=True,
        default=0,
    )
    extra_vars = models.TextField(
        blank=True,
        default='',
    )
    job_tags = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    cancel_flag = models.BooleanField(
        blank=True,
        default=False,
        editable=False,
    )
    launch_type = models.CharField(
        max_length=20,
        choices=LAUNCH_TYPE_CHOICES,
        default='manual',
        editable=False,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        editable=False,
    )
    failed = models.BooleanField(
        default=False,
        editable=False,
    )
    job_args = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        editable=False,
    )
    job_cwd = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        editable=False,
    )
    job_env = JSONField(
        blank=True,
        default={},
        editable=False,
    )
    result_stdout = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    result_traceback = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    celery_task_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        editable=False,
    )
    hosts = models.ManyToManyField(
        'Host',
        related_name='jobs',
        blank=True,
        editable=False,
        through='JobHostSummary',
    )

    def get_absolute_url(self):
        return reverse('main:job_detail', args=(self.pk,))

    def save(self, *args, **kwargs):
        self.failed = bool(self.status in ('failed', 'error', 'canceled'))
        super(Job, self).save(*args, **kwargs)

    @property
    def extra_vars_dict(self):
        '''Return extra_vars key=value pairs as a dictionary.'''
        d = {}
        extra_vars = self.extra_vars.encode('utf-8')
        for kv in [x.decode('utf-8') for x in shlex.split(extra_vars, posix=True)]:
            if '=' in kv:
                k, v = kv.split('=', 1)
                d[k] = v
        return d

    @property
    def celery_task(self):
        try:
            if self.celery_task_id:
                return TaskMeta.objects.get(task_id=self.celery_task_id)
        except TaskMeta.DoesNotExist:
            pass

    @property
    def task_auth_token(self):
        '''Return temporary auth token used for task requests via API.'''
        if self.status == 'running':
            h = hmac.new(settings.SECRET_KEY, self.created.isoformat())
            return '%d-%s' % (self.pk, h.hexdigest())

    def get_passwords_needed_to_start(self):
        '''Return list of password field names needed to start the job.'''
        return (self.credential and self.credential.passwords_needed) or []

    @property
    def can_start(self):
        return bool(self.status == 'new')

    def start(self, **kwargs):
        from awx.main.tasks import RunJob
        if not self.can_start:
            return False
        needed = self.get_passwords_needed_to_start()
        opts = dict([(field, kwargs.get(field, '')) for field in needed])
        if not all(opts.values()):
            return False
        self.status = 'pending'
        self.save(update_fields=['status'])
        task_result = RunJob().delay(self.pk, **opts)
        # Reload job from database so we don't clobber results from RunJob
        # (mainly from tests when using Django 1.4.x).
        job = Job.objects.get(pk=self.pk)
        # The TaskMeta instance in the database isn't created until the worker
        # starts processing the task, so we can only store the task ID here.
        job.celery_task_id = task_result.task_id
        job.save(update_fields=['celery_task_id'])
        return True

    @property
    def can_cancel(self):
        return bool(self.status in ('pending', 'running'))

    def cancel(self):
        if self.can_cancel:
            if not self.cancel_flag:
                self.cancel_flag = True
                self.save(update_fields=['cancel_flag'])
        return self.cancel_flag

    @property
    def successful_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__ok__gt=0)

    @property
    def failed_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__failures__gt=0)

    @property
    def changed_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__changed__gt=0)

    @property
    def dark_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__dark__gt=0)

    @property
    def unreachable_hosts(self):
        return self.dark_hosts

    @property
    def skipped_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__skipped__gt=0)

    @property
    def processed_hosts(self):
        return Host.objects.filter(job_host_summaries__job__pk=self.pk,
                                   job_host_summaries__processed__gt=0)

class JobHostSummary(models.Model):
    '''
    Per-host statistics for each job.
    '''

    class Meta:
        unique_together = [('job', 'host')]
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
        on_delete=models.CASCADE,
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
        return '%s changed=%d dark=%d failures=%d ok=%d processed=%d skipped=%s' % \
            (self.host.name, self.changed, self.dark, self.failures, self.ok,
             self.processed, self.skipped)

    def get_absolute_url(self):
        return reverse('main:job_host_summary_detail', args=(self.pk,))

    def save(self, *args, **kwargs):
        self.failed = bool(self.dark or self.failures)
        super(JobHostSummary, self).save(*args, **kwargs)
        self.update_host_last_job_summary()

    def update_host_last_job_summary(self):
        update_fields = []
        if self.host.last_job != self.job:
            self.host.last_job = self.job
            update_fields.append('last_job')
        if self.host.last_job_host_summary != self:
            self.host.last_job_host_summary = self
            update_fields.append('last_job_host_summary')
        if update_fields:
            self.host.save(update_fields=update_fields)
        self.host.update_has_active_failures()

class JobEvent(models.Model):
    '''
    An event/message logged from the callback when running a job.
    '''

    # Playbook events will be structured to form the following hierarchy:
    # - playbook_on_start (once for each playbook file)
    #   - playbook_on_vars_prompt (for each play, but before play starts, we
    #     currently don't handle responding to these prompts)
    #   - playbook_on_play_start
    #     - playbook_on_import_for_host
    #     - playbook_on_not_import_for_host
    #     - playbook_on_no_hosts_matched
    #     - playbook_on_no_hosts_remaining
    #     - playbook_on_setup
    #       - runner_on*
    #     - playbook_on_task_start
    #       - runner_on_failed
    #       - runner_on_ok
    #       - runner_on_error
    #       - runner_on_skipped
    #       - runner_on_unreachable
    #       - runner_on_no_hosts
    #       - runner_on_async_poll
    #       - runner_on_async_ok
    #       - runner_on_async_failed
    #       - runner_on_file_diff
    #     - playbook_on_notify
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
        (3, 'runner_on_async_ok', _('Host OK'), False),
        (3, 'runner_on_async_failed', _('Host Failure'), True),
        # AWX does not yet support --diff mode
        (3, 'runner_on_file_diff', _('File Difference'), False),
        (0, 'playbook_on_start', _('Playbook Started'), False),
        (2, 'playbook_on_notify', _('Running Handlers'), False),
        (2, 'playbook_on_no_hosts_matched', _('No Hosts Matched'), False),
        (2, 'playbook_on_no_hosts_remaining', _('No Hosts Remaining'), False),
        (2, 'playbook_on_task_start', _('Task Started'), False),
        # AWX does not yet support vars_prompt (and will probably hang :)
        (1, 'playbook_on_vars_prompt', _('Variables Prompted'), False),
        (2, 'playbook_on_setup', _('Gathering Facts'), False),
        # callback will not record this
        (2, 'playbook_on_import_for_host', _('internal: on Import for Host'), False),
        # callback will not record this
        (2, 'playbook_on_not_import_for_host', _('internal: on Not Import for Host'), False),
        (1, 'playbook_on_play_start', _('Play Started'), False),
        (1, 'playbook_on_stats', _('Playbook Complete'), False),
    ]
    FAILED_EVENTS = [x[1] for x in EVENT_TYPES if x[3]]
    EVENT_CHOICES = [(x[1], x[2]) for x in EVENT_TYPES]
    LEVEL_FOR_EVENT = dict([(x[1], x[0]) for x in EVENT_TYPES])

    class Meta:
        app_label = 'main'
        ordering = ('pk',)

    job = models.ForeignKey(
        'Job',
        related_name='job_events',
        on_delete=models.CASCADE,
        editable=False,
    )
    created = models.DateTimeField(
        auto_now_add=True,
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
    host = models.ForeignKey(
        'Host',
        related_name='job_events_as_primary_host',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        editable=False,
    )
    hosts = models.ManyToManyField(
        'Host',
        related_name='job_events',
        blank=True,
        editable=False,
    )
    play = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        editable=False,
    )
    task = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        editable=False,
    )
    parent = models.ForeignKey(
        'self',
        related_name='children',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        editable=False,
    )

    def get_absolute_url(self):
        return reverse('main:job_event_detail', args=(self.pk,))

    def __unicode__(self):
        return u'%s @ %s' % (self.get_event_display(), self.created.isoformat())

    @property
    def event_level(self):
        return self.LEVEL_FOR_EVENT.get(self.event, 0)

    def get_event_display2(self):
        msg = self.get_event_display()
        if self.event == 'playbook_on_play_start':
            if self.play is not None:
                msg = "%s (%s)" % (msg, self.play)
        elif self.event == 'playbook_on_task_start':
            if self.task is not None:
                msg = "%s (%s)" % (msg, self.task)
        return msg

    def _find_parent(self):
        parent_events = set()
        if self.event in ('playbook_on_play_start', 'playbook_on_stats',
                          'playbook_on_vars_prompt'):
            parent_events.add('playbook_on_start')
        elif self.event in ('playbook_on_notify', 'playbook_on_setup',
                            'playbook_on_task_start',
                            'playbook_on_no_hosts_matched',
                            'playbook_on_no_hosts_remaining',
                            'playbook_on_import_for_host',
                            'playbook_on_not_import_for_host'):
            parent_events.add('playbook_on_play_start')
        elif self.event.startswith('runner_on_'):
            parent_events.add('playbook_on_setup')
            parent_events.add('playbook_on_task_start')
        if parent_events:
            try:
                qs = self.job.job_events.all()
                if self.pk:
                    qs = qs.filter(pk__lt=self.pk, event__in=parent_events)
                else:
                    qs = qs.filter(event__in=parent_events)
                return qs.order_by('-pk')[0]
            except IndexError:
                pass
        return None

    def save(self, *args, **kwargs):
        if self.event in self.FAILED_EVENTS:
            self.failed = True
        res = self.event_data.get('res', None)
        if isinstance(res, dict) and res.get('changed', False):
            self.changed = True
        if self.event == 'playbook_on_stats':
            try:
                failures_dict = self.event_data.get('failures', {})
                self.failed = bool(sum(failures_dict.values()))
                changed_dict = self.event_data.get('changed', {})
                self.changed = bool(sum(changed_dict.values()))
            except (AttributeError, TypeError):
                pass
        try:
            if not self.host and self.event_data.get('host', ''):
                self.host = self.job.inventory.hosts.get(name=self.event_data['host'])
        except (Host.DoesNotExist, AttributeError):
            pass
        self.play = self.event_data.get('play', '')
        self.task = self.event_data.get('task', '')
        self.parent = self._find_parent()
        super(JobEvent, self).save(*args, **kwargs)
        self.update_parent_failed_and_changed()
        self.update_hosts()
        self.update_host_summary_from_stats()

    def update_parent_failed_and_changed(self):
        # Propagage failed and changed flags to parent events.
        if self.parent:
            parent = self.parent
            save_parent = False
            if self.failed and not parent.failed:
                parent.failed = True
                save_parent = True
            if self.changed and not parent.changed:
                parent.changed = True
                save_parent = True
            if save_parent:
                parent.save()
                parent.update_parent_failed_and_changed()

    def update_hosts(self, extra_hosts=None):
        extra_hosts = extra_hosts or []
        hostnames = set()
        if self.event_data.get('host', ''):
            hostnames.add(self.event_data['host'])
        if self.event == 'playbook_on_stats':
            try:
                for v in self.event_data.values():
                    hostnames.update(v.keys())
            except AttributeError: # In case event_data or v isn't a dict.
                pass
        for hostname in hostnames:
            try:
                host = self.job.inventory.hosts.get(name=hostname)
            except Host.DoesNotExist:
                continue
            self.hosts.add(host)
        for host in extra_hosts:
            self.hosts.add(host)
        if self.parent:
            self.parent.update_hosts(self.hosts.all())

    def update_host_summary_from_stats(self):
        if self.event != 'playbook_on_stats':
            return
        hostnames = set()
        try:
            for v in self.event_data.values():
                hostnames.update(v.keys())
        except AttributeError: # In case event_data or v isn't a dict.
            pass
        for hostname in hostnames:
            try:
                host = self.job.inventory.hosts.get(name=hostname)
            except Host.DoesNotExist:
                continue
            host_summary = self.job.job_host_summaries.get_or_create(host=host)[0]
            host_summary_changed = False
            for stat in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
                try:
                    value = self.event_data.get(stat, {}).get(hostname, 0)
                    if getattr(host_summary, stat) != value:
                        setattr(host_summary, stat, value)
                        host_summary_changed = True
                except AttributeError: # in case event_data[stat] isn't a dict.
                    pass
            if host_summary_changed:
                host_summary.save()

# TODO: reporting (MPD)

# Add mark_inactive method to User model.
def user_mark_inactive(user, save=True):
    '''Use instead of delete to rename and mark users inactive.'''
    if user.is_active:
        # Set timestamp to datetime.isoformat() but without the time zone
        # offse to stay withint the 30 character username limit.
        deleted_ts = now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        user.username = '_d_%s' % deleted_ts
        user.is_active = False
        if save:
            user.save()
User.add_to_class('mark_inactive', user_mark_inactive)

# Add custom methods to User model for permissions checks.
from awx.main.access import *
User.add_to_class('get_queryset', get_user_queryset)
User.add_to_class('can_access', check_user_access)

# Import signal handlers only after models have been defined.
import awx.main.signals

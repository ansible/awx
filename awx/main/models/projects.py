# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

# Python
import datetime
import os
import re
import urlparse

# Django
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_str
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.utils.timezone import now, make_aware, get_default_timezone

# AWX
from awx.lib.compat import slugify
from awx.main.models.base import * # noqa
from awx.main.models.jobs import Job
from awx.main.models.unified_jobs import * # noqa
from awx.main.utils import update_scm_url

__all__ = ['Project', 'ProjectUpdate']


class ProjectOptions(models.Model):

    SCM_TYPE_CHOICES = [
        ('', _('Manual')),
        ('git', _('Git')),
        ('hg', _('Mercurial')),
        ('svn', _('Subversion')),
    ]

    class Meta:
        abstract = True

    # Project files must be available on the server in folders directly
    # beneath the path specified by settings.PROJECTS_ROOT.  There is no way
    # via the API to upload/update a project or its playbooks; this must be
    # done by other means for now.

    @classmethod
    def get_local_path_choices(cls):
        if os.path.exists(settings.PROJECTS_ROOT):
            paths = [x.decode('utf-8') for x in os.listdir(settings.PROJECTS_ROOT)
                     if os.path.isdir(os.path.join(settings.PROJECTS_ROOT, x))
                     and not x.startswith('.') and not x.startswith('_')]
            qs = Project.objects.filter(active=True)
            used_paths = qs.values_list('local_path', flat=True)
            return [x for x in paths if x not in used_paths]
        else:
            return []

    local_path = models.CharField(
        max_length=1024,
        blank=True,
        help_text=_('Local path (relative to PROJECTS_ROOT) containing '
                    'playbooks and related files for this project.')
    )

    scm_type = models.CharField(
        max_length=8,
        choices=SCM_TYPE_CHOICES,
        blank=True,
        default='',
        verbose_name=_('SCM Type'),
    )
    scm_url = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        verbose_name=_('SCM URL'),
    )
    scm_branch = models.CharField(
        max_length=256,
        blank=True,
        default='',
        verbose_name=_('SCM Branch'),
        help_text=_('Specific branch, tag or commit to checkout.'),
    )
    scm_clean = models.BooleanField(
        default=False,
    )
    scm_delete_on_update = models.BooleanField(
        default=False,
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='%(class)ss',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    def clean_scm_type(self):
        return self.scm_type or ''

    def clean_scm_url(self):
        scm_url = unicode(self.scm_url or '')
        if not self.scm_type:
            return ''
        try:
            scm_url = update_scm_url(self.scm_type, scm_url,
                                     check_special_cases=False)
        except ValueError, e:
            raise ValidationError((e.args or ('Invalid SCM URL',))[0])
        scm_url_parts = urlparse.urlsplit(scm_url)
        if self.scm_type and not any(scm_url_parts):
            raise ValidationError('SCM URL is required')
        return unicode(self.scm_url or '')

    def clean_credential(self):
        if not self.scm_type:
            return None
        cred = self.credential
        if cred:
            if cred.kind != 'scm':
                raise ValidationError('Credential kind must be "scm"')
            try:
                scm_url = update_scm_url(self.scm_type, self.scm_url,
                                         check_special_cases=False)
                scm_url_parts = urlparse.urlsplit(scm_url)
                # Prefer the username/password in the URL, if provided.
                scm_username = scm_url_parts.username or cred.username or ''
                if scm_url_parts.password or cred.password:
                    scm_password = '********'
                else:
                    scm_password = ''
                try:
                    update_scm_url(self.scm_type, self.scm_url, scm_username,
                                   scm_password)
                except ValueError, e:
                    raise ValidationError((e.args or ('Invalid credential',))[0])
            except ValueError:
                pass
        return cred

    def get_project_path(self, check_if_exists=True):
        local_path = os.path.basename(self.local_path)
        if local_path and not local_path.startswith('.'):
            proj_path = os.path.join(settings.PROJECTS_ROOT, local_path)
            if not check_if_exists or os.path.exists(smart_str(proj_path)):
                return proj_path

    @property
    def playbooks(self):
        valid_re = re.compile(r'^\s*?-?\s*?(?:hosts|include):\s*?.*?$')
        results = []
        project_path = self.get_project_path()
        if project_path:
            for dirpath, dirnames, filenames in os.walk(smart_str(project_path)):
                for filename in filenames:
                    if os.path.splitext(filename)[-1] not in ['.yml', '.yaml']:
                        continue
                    playbook = os.path.join(dirpath, filename)
                    # Filter files that do not have either hosts or top-level
                    # includes. Use regex to allow files with invalid YAML to
                    # show up.
                    matched = False
                    try:
                        for n, line in enumerate(file(playbook)):
                            if valid_re.match(line):
                                matched = True
                            # Any YAML file can also be encrypted with vault;
                            # allow these to be used as the main playbook.
                            elif n == 0 and line.startswith('$ANSIBLE_VAULT;'):
                                matched = True
                    except IOError:
                        continue
                    if not matched:
                        continue
                    playbook = os.path.relpath(playbook, smart_str(project_path))
                    # Filter files in a roles subdirectory.
                    if 'roles' in playbook.split(os.sep):
                        continue
                    # Filter files in a tasks subdirectory.
                    if 'tasks' in playbook.split(os.sep):
                        continue
                    results.append(playbook)
        return sorted(results, key=lambda x: smart_str(x).lower())


class Project(UnifiedJobTemplate, ProjectOptions):
    '''
    A project represents a playbook git repo that can access a set of inventories
    '''

    class Meta:
        app_label = 'main'
        ordering = ('id',)

    scm_delete_on_next_update = models.BooleanField(
        default=False,
        editable=False,
    )
    scm_update_on_launch = models.BooleanField(
        default=False,
    )
    scm_update_cache_timeout = models.PositiveIntegerField(
        default=0,
        blank=True,
    )

    @classmethod
    def _get_unified_job_class(cls):
        return ProjectUpdate

    @classmethod
    def _get_unified_job_field_names(cls):
        return ['name', 'description', 'local_path', 'scm_type', 'scm_url',
                'scm_branch', 'scm_clean', 'scm_delete_on_update',
                'credential', 'schedule']

    def save(self, *args, **kwargs):
        new_instance = not bool(self.pk)
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # Check if scm_type or scm_url changes.
        if self.pk:
            project_before = self.__class__.objects.get(pk=self.pk)
            if project_before.scm_type != self.scm_type or project_before.scm_url != self.scm_url:
                self.scm_delete_on_next_update = True
                if 'scm_delete_on_next_update' not in update_fields:
                    update_fields.append('scm_delete_on_next_update')
        # Create auto-generated local path if project uses SCM.
        if self.pk and self.scm_type and not self.local_path.startswith('_'):
            slug_name = slugify(unicode(self.name)).replace(u'-', u'_')
            self.local_path = u'_%d__%s' % (int(self.pk), slug_name)
            if 'local_path' not in update_fields:
                update_fields.append('local_path')
        # Do the actual save.
        super(Project, self).save(*args, **kwargs)
        if new_instance:
            update_fields=[]
            # Generate local_path for SCM after initial save (so we have a PK).
            if self.scm_type and not self.local_path.startswith('_'):
                update_fields.append('local_path')
            if update_fields:
                self.save(update_fields=update_fields)
        # If we just created a new project with SCM, start the initial update.
        if new_instance and self.scm_type:
            self.update()

    def _get_current_status(self):
        if self.scm_type:
            if self.current_job and self.current_job.status:
                return self.current_job.status
            elif not self.last_job:
                return 'never updated'
            # inherit the child job status on failure
            elif self.last_job_failed:
                return self.last_job.status
            # Even on a successful child run, a missing project path overides
            # the successful status
            elif not self.get_project_path():
                return 'missing'
            # Return the successful status
            else:
                return self.last_job.status
        elif not self.get_project_path():
            return 'missing'
        else:
            return 'ok'

    def _get_last_job_run(self):
        if self.scm_type and self.last_job:
            return self.last_job.finished
        else:
            project_path = self.get_project_path()
            if project_path:
                try:
                    mtime = os.path.getmtime(smart_str(project_path))
                    dt = datetime.datetime.fromtimestamp(mtime)
                    return make_aware(dt, get_default_timezone())
                except os.error:
                    pass

    def _can_update(self):
        return bool(self.scm_type)

    def _update_unified_job_kwargs(self, **kwargs):
        if self.scm_delete_on_next_update:
            kwargs['scm_delete_on_update'] = True
        return kwargs

    def create_project_update(self, **kwargs):
        return self.create_unified_job(**kwargs)

    @property
    def cache_timeout_blocked(self):
        if not self.last_job_run:
            return False
        if (self.last_job_run + datetime.timedelta(seconds=self.scm_update_cache_timeout)) > now():
            return True
        return False
    
    @property
    def needs_update_on_launch(self):
        if self.active and self.scm_type and self.scm_update_on_launch:
            if not self.last_job_run:
                return True
            if (self.last_job_run + datetime.timedelta(seconds=self.scm_update_cache_timeout)) <= now():
                return True
        return False

    def get_absolute_url(self):
        return reverse('api:project_detail', args=(self.pk,))


class ProjectUpdate(UnifiedJob, ProjectOptions):
    '''
    Internal job for tracking project updates from SCM.
    '''

    class Meta:
        app_label = 'main'

    project = models.ForeignKey(
        'Project',
        related_name='project_updates',
        on_delete=models.CASCADE,
        editable=False,
    )

    @classmethod
    def _get_parent_field_name(cls):
        return 'project'

    @classmethod
    def _get_task_class(cls):
        from awx.main.tasks import RunProjectUpdate
        return RunProjectUpdate

    def is_blocked_by(self, obj):
        if type(obj) == ProjectUpdate:
            if self.project == obj.project:
                return True
        if type(obj) == Job:
            if self.project == obj.project:
                return True
        return False

    def socketio_emit_data(self):
        return dict(project_id=self.project.id)

    @property
    def task_impact(self):
        return 20

    def get_absolute_url(self):
        return reverse('api:project_update_detail', args=(self.pk,))

    def _update_parent_instance(self):
        parent_instance = self._get_parent_instance()
        if parent_instance:
            update_fields = self._update_parent_instance_no_save(parent_instance)
            if self.status in ('successful', 'failed', 'error', 'canceled'):
                if not self.failed and parent_instance.scm_delete_on_next_update:
                    parent_instance.scm_delete_on_next_update = False
                    if 'scm_delete_on_next_update' not in update_fields:
                        update_fields.append('scm_delete_on_next_update')
            parent_instance.save(update_fields=update_fields)

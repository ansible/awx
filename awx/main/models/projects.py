# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import hashlib
import hmac
import json
import logging
import os
import re
import shlex
import uuid

# PyYAML
import yaml

# Django
from django.conf import settings
from django.db import models
from django.db.models import CASCADE, SET_NULL, PROTECT
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now, make_aware, get_default_timezone

# AWX
from awx.lib.compat import slugify
from awx.main.models.base import *

__all__ = ['Project', 'ProjectUpdate']


class Project(CommonModel):
    '''
    A project represents a playbook git repo that can access a set of inventories
    '''

    PROJECT_STATUS_CHOICES = [
        ('ok', 'OK'),
        ('missing', 'Missing'),
        ('never updated', 'Never Updated'),
        ('updating', 'Updating'),
        ('failed', 'Failed'),
        ('successful', 'Successful'),
    ]
        
    SCM_TYPE_CHOICES = [
        ('', _('Manual')),
        ('git', _('Git')),
        ('hg', _('Mercurial')),
        ('svn', _('Subversion')),
    ]
    
    class Meta:
        app_label = 'main'

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
    scm_delete_on_next_update = models.BooleanField(
        default=False,
        editable=False,
    )
    scm_update_on_launch = models.BooleanField(
        default=False,
    )
    credential = models.ForeignKey(
        'Credential',
        related_name='projects',
        blank=True,
        null=True,
        default=None,
    )
    current_update = models.ForeignKey(
        'ProjectUpdate',
        null=True,
        default=None,
        editable=False,
        related_name='project_as_current_update+',
    )
    last_update = models.ForeignKey(
        'ProjectUpdate',
        null=True,
        default=None,
        editable=False,
        related_name='project_as_last_update+',
    )
    last_update_failed = models.BooleanField(
        default=False,
        editable=False,
    )
    last_updated = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
    )
    status = models.CharField(
        max_length=32,
        choices=PROJECT_STATUS_CHOICES,
        default='ok',
        editable=False,
        null=True, # FIXME: Remove
    )

    def save(self, *args, **kwargs):
        new_instance = not bool(self.pk)
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # Check if scm_type or scm_url changes.
        if self.pk:
            project_before = Project.objects.get(pk=self.pk)
            if project_before.scm_type != self.scm_type or project_before.scm_url != self.scm_url:
                self.scm_delete_on_next_update = True
                if 'scm_delete_on_next_update' not in update_fields:
                    update_fields.append('scm_delete_on_next_update')
        # Create auto-generated local path if project uses SCM.
        if self.pk and self.scm_type and not self.local_path.startswith('_'):
            slug_name = slugify(unicode(self.name)).replace(u'-', u'_')
            self.local_path = u'_%d__%s' % (self.pk, slug_name)
            if 'local_path' not in update_fields:
                update_fields.append('local_path')
        # Update status and last_updated fields.
        updated_fields = self.set_status_and_last_updated(save=False)
        for field in updated_fields:
            if field not in update_fields:
                update_fields.append(field)
        # Do the actual save.
        super(Project, self).save(*args, **kwargs)
        if new_instance:
            update_fields=[]
            # Generate local_path for SCM after initial save (so we have a PK).
            if self.scm_type and not self.local_path.startswith('_'):
                update_fields.append('local_path')
            if update_fields:
                self.save(update_fields=update_fields)
        # If we just created a new project with SCM and it doesn't require any
        # passwords to update, start the initial update.
        if new_instance and self.scm_type and not self.scm_passwords_needed:
            self.update()

    @property
    def needs_scm_password(self):
        return self.credential and self.credential.needs_password

    @property
    def needs_scm_key_unlock(self):
        return self.credential and self.credential.needs_ssh_key_unlock

    @property
    def scm_passwords_needed(self):
        needed = []
        for field in ('scm_password', 'scm_key_unlock'):
            if getattr(self, 'needs_%s' % field):
                needed.append(field)
        return needed

    def set_status_and_last_updated(self, save=True):
        # Determine current status.
        if self.scm_type:
            if self.current_update:
                status = 'updating'
            elif not self.last_update:
                status = 'never updated'
            elif self.last_update_failed:
                status = 'failed'
            elif not self.get_project_path():
                status = 'missing'
            else:
                status = 'successful'
        elif not self.get_project_path():
            status = 'missing'
        else:
            status = 'ok'
        # Determine current last_updated timestamp.
        last_updated = None
        if self.scm_type and self.last_update:
            last_updated = self.last_update.modified
        else:
            project_path = self.get_project_path()
            if project_path:
                try:
                    mtime = os.path.getmtime(project_path)
                    dt = datetime.datetime.fromtimestamp(mtime)
                    last_updated = make_aware(dt, get_default_timezone())
                except os.error:
                    pass
        # Update values if changed.
        update_fields = []
        if self.status != status:
            self.status = status
            update_fields.append('status')
        if self.last_updated != last_updated:
            self.last_updated = last_updated
            update_fields.append('last_updated')
        if save and update_fields:
            self.save(update_fields=update_fields)
        return update_fields

    @property
    def can_update(self):
        # FIXME: Prevent update when another one is active!
        return bool(self.scm_type)# and not self.current_update)

    def update(self, **kwargs):
        if self.can_update:
            needed = self.scm_passwords_needed
            opts = dict([(field, kwargs.get(field, '')) for field in needed])
            if not all(opts.values()):
                return
            project_update = self.project_updates.create()
            project_update.start(**opts)
            return project_update

    def get_absolute_url(self):
        return reverse('api:project_detail', args=(self.pk,))

    def get_project_path(self, check_if_exists=True):
        local_path = os.path.basename(self.local_path)
        if local_path and not local_path.startswith('.'):
            proj_path = os.path.join(settings.PROJECTS_ROOT, local_path)
            if not check_if_exists or os.path.exists(proj_path):
                return proj_path

    @property
    def playbooks(self):
        valid_re = re.compile(r'^\s*?-?\s*?(?:hosts|include):\s*?.*?$')
        results = []
        project_path = self.get_project_path()
        if project_path:
            for dirpath, dirnames, filenames in os.walk(project_path):
                for filename in filenames:
                    if os.path.splitext(filename)[-1] != '.yml':
                        continue
                    playbook = os.path.join(dirpath, filename)
                    # Filter files that do not have either hosts or top-level
                    # includes. Use regex to allow files with invalid YAML to
                    # show up.
                    matched = False
                    try:
                        for line in file(playbook):
                            if valid_re.match(line):
                                matched = True
                    except IOError:
                        continue
                    if not matched:
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

class ProjectUpdate(CommonTask):
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

    def get_absolute_url(self):
        return reverse('api:project_update_detail', args=(self.pk,))

    def _get_parent_instance(self):
        return self.project

    def _get_task_class(self):
        from awx.main.tasks import RunProjectUpdate
        return RunProjectUpdate

    def _get_passwords_needed_to_start(self):
        return self.project.scm_passwords_needed

    def _update_parent_instance(self):
        parent_instance = self._get_parent_instance()
        if parent_instance:
            if self.status in ('pending', 'waiting', 'running'):
                if parent_instance.current_update != self:
                    parent_instance.current_update = self
                    parent_instance.save(update_fields=['current_update'])
            elif self.status in ('successful', 'failed', 'error', 'canceled'):
                if parent_instance.current_update == self:
                    parent_instance.current_update = None
                parent_instance.last_update = self
                parent_instance.last_update_failed = self.failed
                if not self.failed and parent_instance.scm_delete_on_next_update:
                    parent_instance.scm_delete_on_next_update = False
                parent_instance.save(update_fields=['current_update',
                                                    'last_update',
                                                    'last_update_failed',
                                                    'scm_delete_on_next_update'])

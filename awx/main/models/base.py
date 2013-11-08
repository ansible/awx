# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import json
import shlex

# PyYAML
import yaml

# Django
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now

# Django-JSONField
from jsonfield import JSONField

# Django-Taggit
from taggit.managers import TaggableManager

# Django-Celery
from djcelery.models import TaskMeta

__all__ = ['VarsDictProperty', 'PrimordialModel', 'CommonModel', 'ActivityStream',
           'CommonModelNameNotUnique', 'CommonTask', 'PERM_INVENTORY_ADMIN',
           'PERM_INVENTORY_READ', 'PERM_INVENTORY_WRITE',
           'PERM_INVENTORY_DEPLOY', 'PERM_INVENTORY_CHECK', 'JOB_TYPE_CHOICES',
           'PERMISSION_TYPE_CHOICES', 'TASK_STATUS_CHOICES',
           'CLOUD_INVENTORY_SOURCES']

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

TASK_STATUS_CHOICES = [
    ('new', _('New')),                  # Job has been created, but not started.
    ('pending', _('Pending')),          # Job has been queued, but is not yet running.
    ('waiting', _('Waiting')),          # Job is waiting on an update/dependency.
    ('running', _('Running')),          # Job is currently running.
    ('successful', _('Successful')),    # Job completed successfully.
    ('failed', _('Failed')),            # Job completed, but with failures.
    ('error', _('Error')),              # The job was unable to run.
    ('canceled', _('Canceled')),        # The job was canceled before completion.
]

CLOUD_INVENTORY_SOURCES = ['ec2', 'rackspace']


class VarsDictProperty(object):
    '''
    Retrieve a string of variables in YAML or JSON as a dictionary.
    '''

    def __init__(self, field='variables', key_value=False):
        self.field = field
        self.key_value = key_value

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        v = getattr(obj, self.field).encode('utf-8')
        d = None
        try:
            d = json.loads(v.strip() or '{}')
        except ValueError:
            pass
        if d is None:
            try:
                d = yaml.safe_load(v)
            except yaml.YAMLError:
                pass
        if d is None and self.key_value:
            d = {}
            for kv in [x.decode('utf-8') for x in shlex.split(v, posix=True)]:
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    d[k] = v
        return d if hasattr(d, 'items') else {}

    def __set__(self, obj, value):
        raise AttributeError('readonly property')


class PrimordialModel(models.Model):
    '''
    common model for all object types that have these standard fields
    must use a subclass CommonModel or CommonModelNameNotUnique though
    as this lacks a name field.
    '''

    class Meta:
        abstract = True

    description = models.TextField(
        blank=True,
        default='',
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )
    modified = models.DateTimeField(
        auto_now=True,
        default=now,
    )
    created_by = models.ForeignKey(
        'auth.User',
        related_name='%s(class)s_created+',
        default=None,
        null=True,
        editable=False,
        on_delete=models.SET_NULL,
    )
    modified_by = models.ForeignKey(
        'auth.User',
        related_name='%s(class)s_modified+',
        default=None,
        null=True,
        editable=False,
        on_delete=models.SET_NULL,
    )
    active = models.BooleanField(
        default=True,
    )

    tags = TaggableManager(blank=True)

    def __unicode__(self):
        if hasattr(self, 'name'):
            return u'%s-%s' % (self.name, self.id)
        else:
            return u'%s-%s' % (self._meta.verbose_name, self.id)

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

    name = models.CharField(
        max_length=512,
        unique=True,
    )


class CommonModelNameNotUnique(PrimordialModel):
    ''' a base model where the name is not unique '''

    class Meta:
        abstract = True

    name = models.CharField(
        max_length=512,
        unique=False,
    )


class CommonTask(PrimordialModel):
    '''
    Common fields for models run by the task engine.
    '''

    class Meta:
        app_label = 'main'
        abstract = True

    cancel_flag = models.BooleanField(
        blank=True,
        default=False,
        editable=False,
    )
    status = models.CharField(
        max_length=20,
        choices=TASK_STATUS_CHOICES,
        default='new',
        editable=False,
    )
    failed = models.BooleanField(
        default=False,
        editable=False,
    )
    job_args = models.TextField(
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

    def __unicode__(self):
        return u'%s-%s-%s' % (self.created, self.id, self.status)

    def _get_parent_instance(self):
        return None

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
                parent_instance.save(update_fields=['current_update',
                                                    'last_update',
                                                    'last_update_failed'])

    def save(self, *args, **kwargs):
        # Get status before save...
        status_before = self.status or 'new'
        if self.pk:
            self_before = self.__class__.objects.get(pk=self.pk)
            if self_before.status != self.status:
                status_before = self_before.status
        self.failed = bool(self.status in ('failed', 'error', 'canceled'))
        super(CommonTask, self).save(*args, **kwargs)
        # If status changed, update parent instance....
        if self.status != status_before:
            self._update_parent_instance()

    @property
    def celery_task(self):
        try:
            if self.celery_task_id:
                return TaskMeta.objects.get(task_id=self.celery_task_id)
        except TaskMeta.DoesNotExist:
            pass

    @property
    def can_start(self):
        return bool(self.status == 'new')

    def _get_task_class(self):
        raise NotImplementedError

    def _get_passwords_needed_to_start(self):
        return []

    def start(self, **kwargs):
        task_class = self._get_task_class()
        if not self.can_start:
            return False
        needed = self._get_passwords_needed_to_start()
        opts = dict([(field, kwargs.get(field, '')) for field in needed])
        if not all(opts.values()):
            return False
        self.status = 'pending'
        self.save(update_fields=['status'])
        task_result = task_class().delay(self.pk, **opts)
        # Reload instance from database so we don't clobber results from task
        # (mainly from tests when using Django 1.4.x).
        instance = self.__class__.objects.get(pk=self.pk)
        # The TaskMeta instance in the database isn't created until the worker
        # starts processing the task, so we can only store the task ID here.
        instance.celery_task_id = task_result.task_id
        instance.save(update_fields=['celery_task_id'])
        return True

    @property
    def can_cancel(self):
        return bool(self.status in ('pending', 'waiting', 'running'))

    def cancel(self):
        # FIXME: Force cancel!
        if self.can_cancel:
            if not self.cancel_flag:
                self.cancel_flag = True
                self.save(update_fields=['cancel_flag'])
        return self.cancel_flag

class ActivityStream(models.Model):
    '''
    Model used to describe activity stream (audit) events
    '''
    OPERATION_CHOICES = [
        ('create', _('Entity Created')),
        ('update', _("Entity Updated")),
        ('delete', _("Entity Deleted")),
        ('associate', _("Entity Associated with another Entity")),
        ('disaassociate', _("Entity was Disassociated with another Entity"))
    ]

    user = models.ForeignKey('auth.User', null=True, on_delete=models.SET_NULL)
    operation = models.CharField(max_length=9, choices=OPERATION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.TextField(blank=True)

    object1_id = models.PositiveIntegerField(db_index=True)
    object1_type = models.TextField()

    object2_id = models.PositiveIntegerField(db_index=True)
    object2_type = models.TextField()

    object_relationship_type = models.TextField()

# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import json
import shlex

# PyYAML
import yaml

# Django
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now

# Django-Taggit
from taggit.managers import TaggableManager

# Django-CRUM
from crum import get_current_user

# Ansible Tower
from awx.main.utils import encrypt_field

__all__ = ['VarsDictProperty', 'BaseModel', 'CreatedModifiedModel',
           'PasswordFieldsModel', 'PrimordialModel', 'CommonModel',
           'CommonModelNameNotUnique',
           'PERM_INVENTORY_ADMIN', 'PERM_INVENTORY_READ',
           'PERM_INVENTORY_WRITE', 'PERM_INVENTORY_DEPLOY',
           'PERM_INVENTORY_CHECK', 'PERM_JOBTEMPLATE_CREATE', 'JOB_TYPE_CHOICES',
           'PERMISSION_TYPE_CHOICES', 'CLOUD_INVENTORY_SOURCES']

PERM_INVENTORY_ADMIN  = 'admin'
PERM_INVENTORY_READ   = 'read'
PERM_INVENTORY_WRITE  = 'write'
PERM_INVENTORY_DEPLOY = 'run'
PERM_INVENTORY_CHECK  = 'check'
PERM_JOBTEMPLATE_CREATE = 'create'

JOB_TYPE_CHOICES = [
    (PERM_INVENTORY_DEPLOY, _('Run')),
    (PERM_INVENTORY_CHECK, _('Check')),
]

PERMISSION_TYPE_CHOICES = [
    (PERM_INVENTORY_READ, _('Read Inventory')),
    (PERM_INVENTORY_WRITE, _('Edit Inventory')),
    (PERM_INVENTORY_ADMIN, _('Administrate Inventory')),
    (PERM_INVENTORY_DEPLOY, _('Deploy To Inventory')),
    (PERM_INVENTORY_CHECK, _('Deploy To Inventory (Dry Run)')),
    (PERM_JOBTEMPLATE_CREATE, _('Create a Job Template')),
]

CLOUD_INVENTORY_SOURCES = ['ec2', 'rax', 'vmware', 'gce', 'azure', 'custom']


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
        v = getattr(obj, self.field)
        if hasattr(v, 'items'):
            return v
        v = v.encode('utf-8')
        d = None
        try:
            d = json.loads(v.strip() or '{}')
        except ValueError:
            pass
        if d is None:
            try:
                d = yaml.safe_load(v)
                # This can happen if the whole file is commented out
                if d is None:
                    d = {}
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


class BaseModel(models.Model):
    '''
    Base model class with common methods for all models.
    '''

    class Meta:
        abstract = True

    def __unicode__(self):
        if hasattr(self, 'name'):
            return u'%s-%s' % (self.name, self.id)
        else:
            return u'%s-%s' % (self._meta.verbose_name, self.id)

    def clean_fields(self, exclude=None):
        '''
        Override default clean_fields to support methods for cleaning
        individual model fields.
        '''
        exclude = exclude or []
        errors = {}
        try:
            super(BaseModel, self).clean_fields(exclude)
        except ValidationError, e:
            errors = e.update_error_dict(errors)
        for f in self._meta.fields:
            if f.name in exclude:
                continue
            if hasattr(self, 'clean_%s' % f.name):
                try:
                    setattr(self, f.name, getattr(self, 'clean_%s' % f.name)())
                except ValidationError, e:
                    errors[f.name] = e.messages
        if errors:
            raise ValidationError(errors)

    def update_fields(self, **kwargs):
        save = kwargs.pop('save', True)
        update_fields = []
        for field, value in kwargs.items():
            if getattr(self, field) != value:
                setattr(self, field, value)
                update_fields.append(field)
        if save and update_fields:
            self.save(update_fields=update_fields)
        return update_fields

    def save(self, *args, **kwargs):
        # For compatibility with Django 1.4.x, attempt to handle any calls to
        # save that pass update_fields.
        try:
            super(BaseModel, self).save(*args, **kwargs)
        except TypeError:
            if 'update_fields' not in kwargs:
                raise
            kwargs.pop('update_fields')
            super(BaseModel, self).save(*args, **kwargs)

class CreatedModifiedModel(BaseModel):
    '''
    Common model with created/modified timestamp fields.  Allows explicitly
    specifying created/modified timestamps in certain cases (migrations, job
    events), calculates automatically if not specified.
    '''

    class Meta:
        abstract = True

    created = models.DateTimeField(
        default=None,
        editable=False,
    )
    modified = models.DateTimeField(
        default=None,
        editable=False,
    )

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields', [])
        # Manually perform auto_now_add and auto_now logic.
        if not self.pk and not self.created:
            self.created = now()
            if 'created' not in update_fields:
                update_fields.append('created')
        if 'modified' not in update_fields or not self.modified:
            self.modified = now()
            update_fields.append('modified')
        super(CreatedModifiedModel, self).save(*args, **kwargs)


class PasswordFieldsModel(BaseModel):
    '''
    Abstract base class for a model with password fields that should be stored
    as encrypted values.
    '''

    PASSWORD_FIELDS = ()

    class Meta:
        abstract = True

    def _password_field_allows_ask(self, field):
        return False # Override in subclasses if needed.

    def mark_inactive(self, save=True):
        '''
        When marking a password model inactive we'll clear sensitive fields
        '''
        for sensitive_field in self.PASSWORD_FIELDS:
            setattr(self, sensitive_field, "")
        self.save()
        super(PasswordFieldsModel, self).mark_inactive(save=save)

    def save(self, *args, **kwargs):
        new_instance = not bool(self.pk)
        # If update_fields has been specified, add our field names to it,
        # if it hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # When first saving to the database, don't store any password field
        # values, but instead save them until after the instance is created.
        # Otherwise, store encrypted values to the database.
        for field in self.PASSWORD_FIELDS:
            if new_instance:
                value = getattr(self, field, '')
                setattr(self, '_saved_%s' % field, value)
                setattr(self, field, '')
            else:
                ask = self._password_field_allows_ask(field)
                encrypted = encrypt_field(self, field, ask)
                setattr(self, field, encrypted)
                if field not in update_fields:
                    update_fields.append(field)
        super(PasswordFieldsModel, self).save(*args, **kwargs)
        # After saving a new instance for the first time, set the password
        # fields and save again.
        if new_instance:
            update_fields = []
            for field in self.PASSWORD_FIELDS:
                saved_value = getattr(self, '_saved_%s' % field, '')
                setattr(self, field, saved_value)
                update_fields.append(field)
            self.save(update_fields=update_fields)


class PrimordialModel(CreatedModifiedModel):
    '''
    Common model for all object types that have these standard fields
    must use a subclass CommonModel or CommonModelNameNotUnique though
    as this lacks a name field.
    '''

    class Meta:
        abstract = True

    description = models.TextField(
        blank=True,
        default='',
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
        editable=False,
    )

    tags = TaggableManager(blank=True)

    def mark_inactive(self, save=True, update_fields=None, skip_active_check=False):
        '''Use instead of delete to rename and mark inactive.'''
        update_fields = update_fields or []
        if skip_active_check or self.active:
            dtnow = now()
            if 'name' in self._meta.get_all_field_names():
                self.name   = "_deleted_%s_%s" % (dtnow.isoformat(), self.name)
                if 'name' not in update_fields:
                    update_fields.append('name')
            self.active = False
            if 'active' not in update_fields:
                update_fields.append('active')
            if save:
                self.save(update_fields=update_fields)
        return update_fields

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields', [])
        user = get_current_user()
        if user and not user.id:
            user = None
        if not self.pk and not self.created_by:
            self.created_by = user
            if 'created_by' not in update_fields:
                update_fields.append('created_by')
        self.modified_by = user
        if 'modified_by' not in update_fields:
            update_fields.append('modified_by')
        super(PrimordialModel, self).save(*args, **kwargs)

    def clean_description(self):
        # Description should always be empty string, never null.
        return self.description or ''


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

# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now

# Django-Taggit
from taggit.managers import TaggableManager

# Django-CRUM
from crum import get_current_user

# AWX
from awx.main.utils import encrypt_field, parse_yaml_or_json
from awx.main.constants import CLOUD_PROVIDERS

__all__ = ['prevent_search', 'VarsDictProperty', 'BaseModel', 'CreatedModifiedModel',
           'PasswordFieldsModel', 'PrimordialModel', 'CommonModel',
           'CommonModelNameNotUnique', 'NotificationFieldsModel',
           'PERM_INVENTORY_DEPLOY', 'PERM_INVENTORY_SCAN',
           'PERM_INVENTORY_CHECK', 'JOB_TYPE_CHOICES',
           'AD_HOC_JOB_TYPE_CHOICES', 'PROJECT_UPDATE_JOB_TYPE_CHOICES',
           'CLOUD_INVENTORY_SOURCES',
           'VERBOSITY_CHOICES']

PERM_INVENTORY_DEPLOY = 'run'
PERM_INVENTORY_CHECK  = 'check'
PERM_INVENTORY_SCAN   = 'scan'

JOB_TYPE_CHOICES = [
    (PERM_INVENTORY_DEPLOY, _('Run')),
    (PERM_INVENTORY_CHECK, _('Check')),
    (PERM_INVENTORY_SCAN, _('Scan')),
]

NEW_JOB_TYPE_CHOICES = [
    (PERM_INVENTORY_DEPLOY, _('Run')),
    (PERM_INVENTORY_CHECK, _('Check')),
]

AD_HOC_JOB_TYPE_CHOICES = [
    (PERM_INVENTORY_DEPLOY, _('Run')),
    (PERM_INVENTORY_CHECK, _('Check')),
]

PROJECT_UPDATE_JOB_TYPE_CHOICES = [
    (PERM_INVENTORY_DEPLOY, _('Run')),
    (PERM_INVENTORY_CHECK, _('Check')),
]

CLOUD_INVENTORY_SOURCES = list(CLOUD_PROVIDERS) + ['scm', 'custom']

VERBOSITY_CHOICES = [
    (0, '0 (Normal)'),
    (1, '1 (Verbose)'),
    (2, '2 (More Verbose)'),
    (3, '3 (Debug)'),
    (4, '4 (Connection Debug)'),
    (5, '5 (WinRM Debug)'),
]


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
        return parse_yaml_or_json(v)

    def __set__(self, obj, value):
        raise AttributeError('readonly property')


class BaseModel(models.Model):
    '''
    Base model class with common methods for all models.
    '''

    class Meta:
        abstract = True

    def __str__(self):
        if 'name' in self.__dict__:
            return u'%s-%s' % (self.name, self.pk)
        else:
            return u'%s-%s' % (self._meta.verbose_name, self.pk)

    def clean_fields(self, exclude=None):
        '''
        Override default clean_fields to support methods for cleaning
        individual model fields.
        '''
        exclude = exclude or []
        errors = {}
        try:
            super(BaseModel, self).clean_fields(exclude)
        except ValidationError as e:
            errors = e.update_error_dict(errors)
        for f in self._meta.fields:
            if f.name in exclude:
                continue
            if hasattr(self, 'clean_%s' % f.name):
                try:
                    setattr(self, f.name, getattr(self, 'clean_%s' % f.name)())
                except ValidationError as e:
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
        update_fields = list(kwargs.get('update_fields', []))
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
                self.encrypt_field(field, ask)
                self.mark_field_for_save(update_fields, field)
        super(PasswordFieldsModel, self).save(*args, **kwargs)
        # After saving a new instance for the first time, set the password
        # fields and save again.
        if new_instance:
            update_fields = []
            for field in self.PASSWORD_FIELDS:
                saved_value = getattr(self, '_saved_%s' % field, '')
                setattr(self, field, saved_value)
                self.mark_field_for_save(update_fields, field)

            from awx.main.signals import disable_activity_stream
            with disable_activity_stream():
                # We've already got an activity stream record for the object
                # creation, there's no need to have an extra one for the
                # secondary save for secrets
                self.save(update_fields=update_fields)

    def encrypt_field(self, field, ask):
        encrypted = encrypt_field(self, field, ask)
        setattr(self, field, encrypted)

    def mark_field_for_save(self, update_fields, field):
        if field not in update_fields:
            update_fields.append(field)


class HasEditsMixin(BaseModel):
    """Mixin which will keep the versions of field values from last edit
    so we can tell if current model has unsaved changes.
    """

    class Meta:
        abstract = True

    @classmethod
    def _get_editable_fields(cls):
        fds = set([])
        for field in cls._meta.concrete_fields:
            if hasattr(field, 'attname'):
                if field.attname == 'id':
                    continue
                elif field.attname.endswith('ptr_id'):
                    # polymorphic fields should always be non-editable, see:
                    # https://github.com/django-polymorphic/django-polymorphic/issues/349
                    continue
                if getattr(field, 'editable', True):
                    fds.add(field.attname)
        return fds

    def _get_fields_snapshot(self, fields_set=None):
        new_values = {}
        if fields_set is None:
            fields_set = self._get_editable_fields()
        for attr, val in self.__dict__.items():
            if attr in fields_set:
                new_values[attr] = val
        return new_values

    def _values_have_edits(self, new_values):
        return any(
            new_values.get(fd_name, None) != self._prior_values_store.get(fd_name, None)
            for fd_name in new_values.keys()
        )


class PrimordialModel(HasEditsMixin, CreatedModifiedModel):
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

    tags = TaggableManager(blank=True)

    def __init__(self, *args, **kwargs):
        r = super(PrimordialModel, self).__init__(*args, **kwargs)
        if self.pk:
            self._prior_values_store = self._get_fields_snapshot()
        else:
            self._prior_values_store = {}
        return r

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields', [])
        user = get_current_user()
        if user and not user.id:
            user = None
        if not self.pk and not self.created_by:
            self.created_by = user
            if 'created_by' not in update_fields:
                update_fields.append('created_by')
        # Update modified_by if any editable fields have changed
        new_values = self._get_fields_snapshot()
        if (not self.pk and not self.modified_by) or self._values_have_edits(new_values):
            self.modified_by = user
            if 'modified_by' not in update_fields:
                update_fields.append('modified_by')
        super(PrimordialModel, self).save(*args, **kwargs)
        self._prior_values_store = new_values

    def clean_description(self):
        # Description should always be empty string, never null.
        return self.description or ''

    def validate_unique(self, exclude=None):
        super(PrimordialModel, self).validate_unique(exclude=exclude)
        model = type(self)
        if not hasattr(model, 'SOFT_UNIQUE_TOGETHER'):
            return
        errors = []
        for ut in model.SOFT_UNIQUE_TOGETHER:
            kwargs = {}
            for field_name in ut:
                kwargs[field_name] = getattr(self, field_name, None)
            try:
                obj = model.objects.get(**kwargs)
            except ObjectDoesNotExist:
                continue
            if not (self.pk and self.pk == obj.pk):
                errors.append(
                    '%s with this (%s) combination already exists.' % (
                        model.__name__,
                        ', '.join(set(ut) - {'polymorphic_ctype'})
                    )
                )
        if errors:
            raise ValidationError(errors)


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


class NotificationFieldsModel(BaseModel):

    class Meta:
        abstract = True

    notification_templates_error = models.ManyToManyField(
        "NotificationTemplate",
        blank=True,
        related_name='%(class)s_notification_templates_for_errors'
    )

    notification_templates_success = models.ManyToManyField(
        "NotificationTemplate",
        blank=True,
        related_name='%(class)s_notification_templates_for_success'
    )

    notification_templates_started = models.ManyToManyField(
        "NotificationTemplate",
        blank=True,
        related_name='%(class)s_notification_templates_for_started'
    )


def prevent_search(relation):
    """
    Used to mark a model field or relation as "restricted from filtering"
    e.g.,

    class AuthToken(BaseModel):
        user = prevent_search(models.ForeignKey(...))
        sensitive_data = prevent_search(models.CharField(...))

    The flag set by this function is used by
    `awx.api.filters.FieldLookupBackend` to block fields and relations that
    should not be searchable/filterable via search query params
    """
    setattr(relation, '__prevent_search__', True)
    return relation


def accepts_json(relation):
    """
    Used to mark a model field as allowing JSON e.g,. JobTemplate.extra_vars
    This is *mostly* used as a way to provide type hints for certain fields
    so that HTTP OPTIONS reports the type data we need for the CLI to allow
    JSON/YAML input.
    """
    setattr(relation, '__accepts_json__', True)
    return relation

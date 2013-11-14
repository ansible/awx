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
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now, make_aware, get_default_timezone

# Django-JSONField
from jsonfield import JSONField

# AWX
from awx.lib.compat import slugify
from awx.main.fields import AutoOneToOneField
from awx.main.utils import encrypt_field, decrypt_field
from awx.main.models.base import *

__all__ = ['Organization', 'Team', 'Permission', 'Credential', 'AuthToken']


class Organization(CommonModel):
    '''
    An organization is the basic unit of multi-tenancy divisions
    '''

    class Meta:
        app_label = 'main'

    users = models.ManyToManyField(
        'auth.User',
        blank=True,
        related_name='organizations',
    )
    admins = models.ManyToManyField(
        'auth.User',
        blank=True,
        related_name='admin_of_organizations',
    )
    projects = models.ManyToManyField(
        'Project',
        blank=True,
        related_name='organizations',
    )

    def get_absolute_url(self):
        return reverse('api:organization_detail', args=(self.pk,))

    def __unicode__(self):
        return self.name


class Team(CommonModelNameNotUnique):
    '''
    A team is a group of users that work on common projects.
    '''

    class Meta:
        app_label = 'main'
        unique_together = [('organization', 'name')]

    projects = models.ManyToManyField(
        'Project',
        blank=True,
        related_name='teams',
    )
    users = models.ManyToManyField(
        'auth.User',
        blank=True,
        related_name='teams',
    )
    organization = models.ForeignKey(
        'Organization',
        blank=False,
        null=True,
        on_delete=models.SET_NULL,
        related_name='teams',
    )

    def get_absolute_url(self):
        return reverse('api:team_detail', args=(self.pk,))


class Permission(CommonModelNameNotUnique):
    '''
    A permission allows a user, project, or team to be able to use an inventory source.
    '''

    class Meta:
        app_label = 'main'

    # permissions are granted to either a user or a team:
    user            = models.ForeignKey('auth.User', null=True, on_delete=models.SET_NULL, blank=True, related_name='permissions')
    team            = models.ForeignKey('Team', null=True, on_delete=models.SET_NULL, blank=True, related_name='permissions')

    # to be used against a project or inventory (or a project and inventory in conjunction):
    project         = models.ForeignKey('Project', null=True, on_delete=models.SET_NULL, blank=True, related_name='permissions')
    inventory       = models.ForeignKey('Inventory', null=True, on_delete=models.SET_NULL, related_name='permissions')

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
        return reverse('api:permission_detail', args=(self.pk,))


class Credential(CommonModelNameNotUnique):
    '''
    A credential contains information about how to talk to a remote resource
    Usually this is a SSH key location, and possibly an unlock password.
    If used with sudo, a sudo password should be set if required.
    '''

    KIND_CHOICES = [
        ('ssh', _('Machine')),
        ('scm', _('SCM')),
        ('aws', _('AWS')),
        ('rax', _('Rackspace')),
    ]

    PASSWORD_FIELDS = ('password', 'ssh_key_data', 'ssh_key_unlock',
                       'sudo_password')

    class Meta:
        app_label = 'main'
        unique_together = [('user', 'team', 'kind', 'name')]

    user = models.ForeignKey(
        'auth.User',
        null=True,
        default=None,
        blank=True,
        on_delete=models.CASCADE,
        related_name='credentials',
    )
    team = models.ForeignKey(
        'Team',
        null=True,
        default=None,
        blank=True,
        on_delete=models.CASCADE,
        related_name='credentials',
    )
    kind = models.CharField(
        max_length=32,
        choices=KIND_CHOICES,
        default='ssh',
    )
    cloud = models.BooleanField(
        default=False,
        editable=False,
    )
    username = models.CharField(
        blank=True,
        default='',
        max_length=1024,
        verbose_name=_('Username'),
        help_text=_('Username for this credential.'),
    )
    password = models.CharField(
        blank=True,
        default='',
        max_length=1024,
        verbose_name=_('Password'),
        help_text=_('Password for this credential.'),
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
    def needs_password(self):
        return not self.ssh_key_data and self.password == 'ASK'

    @property
    def needs_ssh_key_unlock(self):
        return 'ENCRYPTED' in decrypt_field(self, 'ssh_key_data') and \
            (not self.ssh_key_unlock or self.ssh_key_unlock == 'ASK')

    @property
    def needs_sudo_password(self):
        return self.sudo_password == 'ASK'

    @property
    def passwords_needed(self):
        needed = []
        for field in ('password', 'sudo_password', 'ssh_key_unlock'):
            if getattr(self, 'needs_%s' % field):
                needed.append(field)
        return needed

    def get_absolute_url(self):
        return reverse('api:credential_detail', args=(self.pk,))

    def clean(self):
        if self.user and self.team:
            raise ValidationError('Credential cannot be assigned to both a user and team')

    def _validate_unique_together_with_null(self, unique_check, exclude=None):
        # Based on existing Django model validation code, except it doesn't
        # skip the check for unique violations when a field is None.  See:
        # https://github.com/django/django/blob/stable/1.5.x/django/db/models/base.py#L792
        errors = {}
        model_class = self.__class__
        if set(exclude or []) & set(unique_check):
            return
        lookup_kwargs = {}
        for field_name in unique_check:
            f = self._meta.get_field(field_name)
            lookup_value = getattr(self, f.attname)
            if f.primary_key and not self._state.adding:
                # no need to check for unique primary key when editing
                continue
            lookup_kwargs[str(field_name)] = lookup_value
        if len(unique_check) != len(lookup_kwargs):
            return
        qs = model_class._default_manager.filter(**lookup_kwargs)
        # Exclude the current object from the query if we are editing an
        # instance (as opposed to creating a new one)
        # Note that we need to use the pk as defined by model_class, not
        # self.pk. These can be different fields because model inheritance
        # allows single model to have effectively multiple primary keys.
        # Refs #17615.
        model_class_pk = self._get_pk_val(model_class._meta)
        if not self._state.adding and model_class_pk is not None:
            qs = qs.exclude(pk=model_class_pk)
        if qs.exists():
            key = NON_FIELD_ERRORS
            errors.setdefault(key, []).append( \
                self.unique_error_message(model_class, unique_check))
        if errors:
            raise ValidationError(errors)

    def validate_unique(self, exclude=None):
        errors = {}
        try:
            super(Credential, self).validate_unique(exclude)
        except ValidationError, e:
            errors = e.update_error_dict(errors)
        try:
            unique_fields = ('user', 'team', 'kind', 'name')
            self._validate_unique_together_with_null(unique_fields, exclude)
        except ValidationError, e:
            errors = e.update_error_dict(errors)
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        new_instance = not bool(self.pk)
        update_fields = kwargs.get('update_fields', [])
        # When first saving to the database, don't store any password field
        # values, but instead save them until after the instance is created.
        if new_instance:
            for field in self.PASSWORD_FIELDS:
                value = getattr(self, field, '')
                setattr(self, '_saved_%s' % field, value)
                setattr(self, field, '')
        # Otherwise, store encrypted values to the database.
        else:
            # If update_fields has been specified, add our field names to it,
            # if hit hasn't been specified, then we're just doing a normal save.
            for field in self.PASSWORD_FIELDS:
                encrypted = encrypt_field(self, field, bool(field != 'ssh_key_data'))
                setattr(self, field, encrypted)
                if field not in update_fields:
                    update_fields.append(field)
        cloud = self.kind in ('aws', 'rax')
        if self.cloud != cloud:
            self.cloud = cloud
            if 'cloud' not in update_fields:
                update_fields.append('cloud')
        super(Credential, self).save(*args, **kwargs)
        # After saving a new instance for the first time, set the password
        # fields and save again.
        if new_instance:
            update_fields=[]
            for field in self.PASSWORD_FIELDS:
                saved_value = getattr(self, '_saved_%s' % field, '')
                setattr(self, field, saved_value)
                update_fields.append(field)
            self.save(update_fields=update_fields)

class Profile(models.Model):
    '''
    Profile model related to User object. Currently stores LDAP DN for users
    loaded from LDAP.
    '''

    class Meta:
        app_label = 'main'

    created = models.DateTimeField(
        auto_now_add=True,
    )
    modified = models.DateTimeField(
        auto_now=True,
    )
    user = AutoOneToOneField(
        'auth.User',
        related_name='profile',
        editable=False,
    )
    ldap_dn = models.CharField(
        max_length=1024,
        default='',
    )

class AuthToken(models.Model):
    '''
    Custom authentication tokens per user with expiration and request-specific
    data.
    '''

    class Meta:
        app_label = 'main'
    
    key = models.CharField(max_length=40, primary_key=True)
    user = models.ForeignKey('auth.User', related_name='auth_tokens',
                             on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    expires = models.DateTimeField(default=now)
    request_hash = models.CharField(max_length=40, blank=True, default='')

    @classmethod
    def get_request_hash(cls, request):
        h = hashlib.sha1()
        h.update(settings.SECRET_KEY)
        for header in settings.REMOTE_HOST_HEADERS:
            value = request.META.get(header, '').strip()
            if value:
                h.update(value)
        h.update(request.META.get('HTTP_USER_AGENT', ''))
        return h.hexdigest()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.refresh(save=False)
        if not self.key:
            self.key = self.generate_key()
        return super(AuthToken, self).save(*args, **kwargs)

    def refresh(self, save=True):
        if not self.pk or not self.expired:
            self.expires = now() + datetime.timedelta(seconds=settings.AUTH_TOKEN_EXPIRATION)
            if save:
                self.save()

    def invalidate(self, save=True):
        if not self.expired:
            self.expires = now() - datetime.timedelta(seconds=1)
            if save:
                self.save()

    def generate_key(self):
        unique = uuid.uuid4()
        return hmac.new(unique.bytes, digestmod=hashlib.sha1).hexdigest()

    @property
    def expired(self):
        return bool(self.expires < now())

    def __unicode__(self):
        return self.key


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

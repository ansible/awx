# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import base64
import re

# Django
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.core.urlresolvers import reverse

# AWX
from awx.main.utils import decrypt_field
from awx.main.models.base import *

__all__ = ['Credential']


class Credential(PasswordFieldsModel, CommonModelNameNotUnique):
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
                       'sudo_password', 'vault_password')

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
        help_text=_('Password for this credential (or "ASK" to prompt the '
                    'user for machine credentials).'),
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
                    '"ASK" to prompt the user for machine credentials).'),
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
    vault_password = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Vault password (or "ASK" to prompt the user).'),
    )

    @property
    def needs_password(self):
        return self.kind == 'ssh' and self.password == 'ASK'

    @property
    def needs_ssh_key_unlock(self):
        ssh_key_data = ''
        if self.kind == 'ssh' and self.ssh_key_unlock == 'ASK':
            if self.pk:
                ssh_key_data = decrypt_field(self, 'ssh_key_data')
            else:
                ssh_key_data = self.ssh_key_data
        return 'ENCRYPTED' in ssh_key_data

    @property
    def needs_sudo_password(self):
        return self.kind == 'ssh' and self.sudo_password == 'ASK'

    @property
    def needs_vault_password(self):
        return self.kind == 'ssh' and self.vault_password == 'ASK'

    @property
    def passwords_needed(self):
        needed = []
        for field in ('password', 'sudo_password', 'ssh_key_unlock', 'vault_password'):
            if getattr(self, 'needs_%s' % field):
                needed.append(field)
        return needed

    def get_absolute_url(self):
        return reverse('api:credential_detail', args=(self.pk,))

    def clean_username(self):
        username = self.username or ''
        if not username and self.kind == 'aws':
            raise ValidationError('Access key required for "aws" credential')
        if not username and self.kind == 'rax':
            raise ValidationError('Username required for "rax" credential')
        return username

    def clean_password(self):
        password = self.password or ''
        if not password and self.kind == 'aws':
            raise ValidationError('Secret key required for "aws" credential')
        if not password and self.kind == 'rax':
            raise ValidationError('API key required for "rax" credential')
        return password

    def _validate_ssh_private_key(self, data):
        validation_error = ValidationError('Invalid SSH private key')
        begin_re = re.compile(r'^(-{4,})\s*?BEGIN\s([A-Z0-9]+?)\sPRIVATE\sKEY\s*?(-{4,})$')
        header_re = re.compile(r'^(.+?):\s*?(.+?)(\\??)$')
        end_re = re.compile(r'^(-{4,})\s*?END\s([A-Z0-9]+?)\sPRIVATE\sKEY\s*?(-{4,})$')
        lines = data.strip().splitlines()
        if not lines:
            raise validation_error
        begin_match = begin_re.match(lines[0])
        end_match = end_re.match(lines[-1])
        if not begin_match or not end_match:
            raise validation_error
        dashes = set([begin_match.groups()[0], begin_match.groups()[2],
                      end_match.groups()[0], end_match.groups()[2]])
        if len(dashes) != 1:
            raise validation_error
        if begin_match.groups()[1] != end_match.groups()[1]:
            raise validation_error
        line_continues = False
        base64_data = ''
        for line in lines[1:-1]:
            line = line.strip()
            if not line:
                continue
            if line_continues:
                line_continues = line.endswith('\\')
                continue
            line_match = header_re.match(line)
            if line_match:
                line_continues = line.endswith('\\')
                continue
            base64_data += line
        try:
            decoded_data = base64.b64decode(base64_data)
            if not decoded_data:
                raise validation_error
        except TypeError:
            raise validation_error

    def clean_ssh_key_data(self):
        if self.pk:
            ssh_key_data = decrypt_field(self, 'ssh_key_data')
        else:
            ssh_key_data = self.ssh_key_data
        if ssh_key_data:
            self._validate_ssh_private_key(ssh_key_data)
        return self.ssh_key_data # No need to return decrypted version here.

    def clean_ssh_key_unlock(self):
        if self.pk:
            ssh_key_data = decrypt_field(self, 'ssh_key_data')
        else:
            ssh_key_data = self.ssh_key_data
        if 'ENCRYPTED' in ssh_key_data and not self.ssh_key_unlock:
            raise ValidationError('SSH key unlock must be set when SSH key '
                                  'is encrypted')
        return self.ssh_key_unlock

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

    def _password_field_allows_ask(self, field):
        return bool(self.kind == 'ssh' and field != 'ssh_key_data')

    def save(self, *args, **kwargs):
        # If update_fields has been specified, add our field names to it,
        # if hit hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        cloud = self.kind in ('aws', 'rax')
        if self.cloud != cloud:
            self.cloud = cloud
            if 'cloud' not in update_fields:
                update_fields.append('cloud')
        super(Credential, self).save(*args, **kwargs)

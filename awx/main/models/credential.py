# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

# AWX
from awx.main.fields import ImplicitRoleField
from awx.main.constants import CLOUD_PROVIDERS
from awx.main.utils import decrypt_field
from awx.main.validators import validate_ssh_private_key
from awx.main.models.base import * # noqa
from awx.main.models.mixins import ResourceMixin
from awx.main.models.rbac import (
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    ROLE_SINGLETON_SYSTEM_AUDITOR,
)

__all__ = ['Credential']


class Credential(PasswordFieldsModel, CommonModelNameNotUnique, ResourceMixin):
    '''
    A credential contains information about how to talk to a remote resource
    Usually this is a SSH key location, and possibly an unlock password.
    If used with sudo, a sudo password should be set if required.
    '''

    KIND_CHOICES = [
        ('ssh', _('Machine')),
        ('net', _('Network')),
        ('scm', _('Source Control')),
        ('aws', _('Amazon Web Services')),
        ('rax', _('Rackspace')),
        ('vmware', _('VMware vCenter')),
        ('satellite6', _('Red Hat Satellite 6')),
        ('cloudforms', _('Red Hat CloudForms')),
        ('gce', _('Google Compute Engine')),
        ('azure', _('Microsoft Azure Classic (deprecated)')),
        ('azure_rm', _('Microsoft Azure Resource Manager')),
        ('openstack', _('OpenStack')),
    ]

    BECOME_METHOD_CHOICES = [
        ('', _('None')),
        ('sudo', _('Sudo')),
        ('su', _('Su')),
        ('pbrun', _('Pbrun')),
        ('pfexec', _('Pfexec')),
        #('runas',  _('Runas')),
    ]

    PASSWORD_FIELDS = ('password', 'security_token', 'ssh_key_data', 'ssh_key_unlock',
                       'become_password', 'vault_password', 'secret', 'authorize_password')

    class Meta:
        app_label = 'main'
        ordering = ('kind', 'name')
        unique_together = (('organization', 'name', 'kind'),)

    deprecated_user = models.ForeignKey(
        'auth.User',
        null=True,
        default=None,
        blank=True,
        on_delete=models.CASCADE,
        related_name='deprecated_credentials',
    )
    deprecated_team = models.ForeignKey(
        'Team',
        null=True,
        default=None,
        blank=True,
        on_delete=models.CASCADE,
        related_name='deprecated_credentials',
    )
    organization = models.ForeignKey(
        'Organization',
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
    host = models.CharField(
        blank=True,
        default='',
        max_length=1024,
        verbose_name=_('Host'),
        help_text=_('The hostname or IP address to use.'),
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
    security_token = models.CharField(
        blank=True,
        default='',
        max_length=1024,
        verbose_name=_('Security Token'),
        help_text=_('Security Token for this credential'),
    )
    project = models.CharField(
        blank=True,
        default='',
        max_length=100,
        verbose_name=_('Project'),
        help_text=_('The identifier for the project.'),
    )
    domain = models.CharField(
        blank=True,
        default='',
        max_length=100,
        verbose_name=_('Domain'),
        help_text=_('The identifier for the domain.'),
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
    become_method = models.CharField(
        max_length=32,
        blank=True,
        default='',
        choices=BECOME_METHOD_CHOICES,
        help_text=_('Privilege escalation method.')
    )
    become_username = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Privilege escalation username.'),
    )
    become_password = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Password for privilege escalation method.')
    )
    vault_password = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Vault password (or "ASK" to prompt the user).'),
    )
    authorize = models.BooleanField(
        default=False,
        help_text=_('Whether to use the authorize mechanism.'),
    )
    authorize_password = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Password used by the authorize mechanism.'),
    )
    client = models.CharField(
        max_length=128,
        blank=True,
        default='',
        help_text=_('Client Id or Application Id for the credential'),
    )
    secret = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Secret Token for this credential'),
    )
    subscription = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Subscription identifier for this credential'),
    )
    tenant = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_('Tenant identifier for this credential'),
    )
    admin_role = ImplicitRoleField(
        parent_role=[
            'singleton:' + ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
            'organization.admin_role',
        ],
    )
    use_role = ImplicitRoleField(
        parent_role=[
            'admin_role',
        ]
    )
    read_role = ImplicitRoleField(parent_role=[
        'singleton:' + ROLE_SINGLETON_SYSTEM_AUDITOR,
        'organization.auditor_role',
        'use_role',
        'admin_role',
    ])

    @property
    def needs_ssh_password(self):
        return self.kind == 'ssh' and self.password == 'ASK'

    @property
    def has_encrypted_ssh_key_data(self):
        if self.pk:
            ssh_key_data = decrypt_field(self, 'ssh_key_data')
        else:
            ssh_key_data = self.ssh_key_data
        try:
            pem_objects = validate_ssh_private_key(ssh_key_data)
            for pem_object in pem_objects:
                if pem_object.get('key_enc', False):
                    return True
        except ValidationError:
            pass
        return False

    @property
    def needs_ssh_key_unlock(self):
        if self.kind == 'ssh' and self.ssh_key_unlock in ('ASK', ''):
            return self.has_encrypted_ssh_key_data
        return False

    @property
    def needs_become_password(self):
        return self.kind == 'ssh' and self.become_password == 'ASK'

    @property
    def needs_vault_password(self):
        return self.kind == 'ssh' and self.vault_password == 'ASK'

    @property
    def passwords_needed(self):
        needed = []
        for field in ('ssh_password', 'become_password', 'ssh_key_unlock', 'vault_password'):
            if getattr(self, 'needs_%s' % field):
                needed.append(field)
        return needed

    def get_absolute_url(self):
        return reverse('api:credential_detail', args=(self.pk,))

    def clean_host(self):
        """Ensure that if this is a type of credential that requires a
        `host`, that a host is provided.
        """
        host = self.host or ''
        if not host and self.kind == 'vmware':
            raise ValidationError('Host required for VMware credential.')
        if not host and self.kind == 'openstack':
            raise ValidationError('Host required for OpenStack credential.')
        return host

    def clean_domain(self):
        return self.domain or ''

    def clean_username(self):
        username = self.username or ''
        if not username and self.kind == 'aws':
            raise ValidationError('Access key required for AWS credential.')
        if not username and self.kind == 'rax':
            raise ValidationError('Username required for Rackspace '
                                  'credential.')
        if not username and self.kind == 'vmware':
            raise ValidationError('Username required for VMware credential.')
        if not username and self.kind == 'openstack':
            raise ValidationError('Username required for OpenStack credential.')
        return username

    def clean_password(self):
        password = self.password or ''
        if not password and self.kind == 'aws':
            raise ValidationError('Secret key required for AWS credential.')
        if not password and self.kind == 'rax':
            raise ValidationError('API key required for Rackspace credential.')
        if not password and self.kind == 'vmware':
            raise ValidationError('Password required for VMware credential.')
        if not password and self.kind == 'openstack':
            raise ValidationError('Password or API key required for OpenStack credential.')
        return password

    def clean_project(self):
        project = self.project or ''
        if self.kind == 'openstack' and not project:
            raise ValidationError('Project name required for OpenStack credential.')
        return project

    def clean_ssh_key_data(self):
        if self.pk:
            ssh_key_data = decrypt_field(self, 'ssh_key_data')
        else:
            ssh_key_data = self.ssh_key_data
        if ssh_key_data:
            # Sanity check: GCE, in particular, provides JSON-encoded private
            # keys, which developers will be tempted to copy and paste rather
            # than JSON decode.
            #
            # These end in a unicode-encoded final character that gets double
            # escaped due to being in a Python 2 bytestring, and that causes
            # Python's key parsing to barf. Detect this issue and correct it.
            if r'\u003d' in ssh_key_data:
                ssh_key_data = ssh_key_data.replace(r'\u003d', '=')
                self.ssh_key_data = ssh_key_data

            # Validate the private key to ensure that it looks like something
            # that we can accept.
            validate_ssh_private_key(ssh_key_data)
        return self.ssh_key_data # No need to return decrypted version here.

    def clean_ssh_key_unlock(self):
        if self.has_encrypted_ssh_key_data and not self.ssh_key_unlock:
            raise ValidationError('SSH key unlock must be set when SSH key '
                                  'is encrypted.')
        return self.ssh_key_unlock

    def clean(self):
        if self.deprecated_user and self.deprecated_team:
            raise ValidationError('Credential cannot be assigned to both a user and team.')

    def _password_field_allows_ask(self, field):
        return bool(self.kind == 'ssh' and field != 'ssh_key_data')

    def save(self, *args, **kwargs):
        # If update_fields has been specified, add our field names to it,
        # if hit hasn't been specified, then we're just doing a normal save.
        update_fields = kwargs.get('update_fields', [])
        # If updating a credential, make sure that we only allow user OR team
        # to be set, and clear out the other field based on which one has
        # changed.
        if self.pk:
            cred_before = Credential.objects.get(pk=self.pk)
            if self.deprecated_user and self.deprecated_team:
                # If the user changed, remove the previously assigned team.
                if cred_before.user != self.user:
                    self.deprecated_team = None
                    if 'deprecated_team' not in update_fields:
                        update_fields.append('deprecated_team')
                # If the team changed, remove the previously assigned user.
                elif cred_before.deprecated_team != self.deprecated_team:
                    self.deprecated_user = None
                    if 'deprecated_user' not in update_fields:
                        update_fields.append('deprecated_user')
        # Set cloud flag based on credential kind.
        cloud = self.kind in CLOUD_PROVIDERS + ('aws',)
        if self.cloud != cloud:
            self.cloud = cloud
            if 'cloud' not in update_fields:
                update_fields.append('cloud')
        super(Credential, self).save(*args, **kwargs)
